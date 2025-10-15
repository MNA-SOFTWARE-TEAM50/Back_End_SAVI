"""
API de Devoluciones
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, date, time
from typing import List
import csv
import io
from fastapi.responses import StreamingResponse

from db.session import get_db
from core.security import get_current_user
from core.config import settings
from models.sale import Sale
from models.product import Product
from models.returns import Return as ReturnModel
from models.audit_log import AuditLog
from models.user import User
from schemas.returns import Return as ReturnSchema, ReturnCreate, ReturnList, ReturnValidation

router = APIRouter()


def _parse_date_range(date_from: str | None, date_to: str | None):
    start_dt = None
    end_dt = None
    try:
        if date_from:
            if len(date_from) <= 10:
                d = date.fromisoformat(date_from)
                start_dt = datetime.combine(d, time.min)
            else:
                start_dt = datetime.fromisoformat(date_from)
        if date_to:
            if len(date_to) <= 10:
                d = date.fromisoformat(date_to)
                end_dt = datetime.combine(d, time.max)
            else:
                end_dt = datetime.fromisoformat(date_to)
    except Exception:
        pass
    return start_dt, end_dt


@router.get("/validate", response_model=ReturnValidation)
async def validate_return(
    sale_id: int = Query(..., description="ID de venta"),
    now: datetime | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Valida si una venta es elegible para devolución conforme a ventana de días y estado."""
    result = await db.execute(select(Sale).where(Sale.id == sale_id))
    sale = result.scalar_one_or_none()
    if not sale:
        return ReturnValidation(ok=False, reason="Venta no encontrada")

    # ventana de días
    created = sale.created_at or datetime.utcnow()
    now = now or datetime.utcnow()
    delta = now - created
    if delta.days > settings.RETURN_WINDOW_DAYS:
        return ReturnValidation(ok=False, reason=f"Fuera de ventana de {settings.RETURN_WINDOW_DAYS} días")

    # estado permitido
    if sale.status not in ("completed",):
        return ReturnValidation(ok=False, reason="Estado de venta no permite devolución")

    return ReturnValidation(ok=True)


@router.post("/", response_model=ReturnSchema, status_code=status.HTTP_201_CREATED)
async def create_return(
    payload: ReturnCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crea una devolución con reglas: valida ventana, estado, calcula montos, ajusta stock atómicamente y registra comprobante."""
    # Obtener venta
    result = await db.execute(select(Sale).where(Sale.id == payload.sale_id))
    sale = result.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    # Ventana de días
    created = sale.created_at or datetime.utcnow()
    if (datetime.utcnow() - created).days > settings.RETURN_WINDOW_DAYS:
        raise HTTPException(status_code=400, detail=f"Fuera de ventana de {settings.RETURN_WINDOW_DAYS} días")

    # Permitir solo si estado completed
    if sale.status != "completed":
        raise HTTPException(status_code=400, detail="Estado de venta no permite devolución")

    # Mapear items de la venta por product_id para validar cantidades y precios
    sale_items = {}
    try:
        for it in sale.items or []:
            if isinstance(it, dict):
                pid = int(it.get("product_id"))
                sale_items[pid] = {
                    "name": it.get("product_name"),
                    "quantity": int(it.get("quantity", 0)),
                    "unit_price": float(it.get("unit_price", 0)),
                    "subtotal": float(it.get("subtotal", 0)),
                }
    except Exception:
        raise HTTPException(status_code=400, detail="Formato de items en venta inválido")

    # Obtener devoluciones previas de esta venta para no exceder vendido
    prev_res = await db.execute(select(ReturnModel).where(ReturnModel.sale_id == sale.id))
    prev_returns = prev_res.scalars().all()
    prev_by_pid: dict[int, int] = {}
    for r in prev_returns:
        try:
            for it in (r.items_returned or []):
                if isinstance(it, dict):
                    pid = int(it.get("product_id"))
                    prev_by_pid[pid] = prev_by_pid.get(pid, 0) + int(it.get("quantity", 0))
        except Exception:
            pass

    # Validar items a devolver no exceden vendidos y calcular montos
    subtotal_ref = 0.0
    tax_ref = 0.0
    total_ref = 0.0

    for rit in payload.items_returned:
        if rit.product_id not in sale_items:
            raise HTTPException(status_code=400, detail=f"Producto {rit.product_id} no pertenece a la venta")
        sold = sale_items[rit.product_id]
        already = prev_by_pid.get(rit.product_id, 0)
        if rit.quantity <= 0 or (rit.quantity + already) > sold["quantity"]:
            raise HTTPException(status_code=400, detail=f"Cantidad inválida para {sold['name']}")
        # base: usamos unit_price de la venta; subtotal de request puede ignorarse
        line_sub = sold["unit_price"] * rit.quantity
        subtotal_ref += line_sub

    # Si hay intercambio, no reembolsamos dinero, solo ajustamos stock diferenciado
    action = payload.action
    refund_method = payload.refund_method
    if action == "refund":
        if not refund_method:
            raise HTTPException(status_code=400, detail="refund_method requerido para reembolso")
        # Debe coincidir con método original
        if refund_method != sale.payment_method:
            raise HTTPException(status_code=400, detail="El reembolso debe ser por el mismo método de pago de la venta")

    # Proporción de impuestos basada en ratio venta
    tax_ratio = 0.0
    try:
        tax_ratio = (sale.tax / sale.subtotal) if sale.subtotal > 0 else 0.0
    except Exception:
        tax_ratio = 0.0
    tax_ref = round(subtotal_ref * tax_ratio, 2)
    total_ref = round(subtotal_ref + tax_ref, 2)

    # En caso de intercambio, forzar totales de reembolso a 0
    if action == "exchange":
        subtotal_ref = 0.0
        tax_ref = 0.0
        total_ref = 0.0

    # Ajuste de stock en una sola transacción: incrementar devueltos, decrementar intercambiados (si aplica)
    # Incrementar inventario por devueltos
    for rit in payload.items_returned:
        res = await db.execute(select(Product).where(Product.id == rit.product_id))
        prod = res.scalar_one_or_none()
        if not prod:
            raise HTTPException(status_code=404, detail=f"Producto {rit.product_id} no encontrado")
        prod.stock += int(rit.quantity)

    # Decrementar inventario por items de intercambio
    if payload.items_exchanged:
        for eit in payload.items_exchanged:
            res = await db.execute(select(Product).where(Product.id == eit.product_id))
            prod = res.scalar_one_or_none()
            if not prod:
                raise HTTPException(status_code=404, detail=f"Producto {eit.product_id} no encontrado")
            if prod.stock < int(eit.quantity):
                raise HTTPException(status_code=400, detail=f"Stock insuficiente para intercambio de {prod.name}")
            prod.stock -= int(eit.quantity)

    # Crear devolución
    db_return = ReturnModel(
        sale_id=sale.id,
        user_id=current_user.id,
        items_returned=[ri.model_dump() for ri in payload.items_returned],
        items_exchanged=[ei.model_dump() for ei in payload.items_exchanged] if payload.items_exchanged else None,
        subtotal_refund=round(subtotal_ref, 2),
        tax_refund=tax_ref,
        total_refund=total_ref,
        action=action,
        refund_method=refund_method,
        reason=payload.reason or None,
        status="completed",
    )
    db.add(db_return)

    # Nota: procesar reembolso real (p.ej., tarjeta) queda fuera de alcance; aquí registramos intención.

    await db.flush()
    await db.refresh(db_return)

    # Registrar auditoría
    try:
        detail = f"ReturnID={db_return.id}, SaleID={sale.id}, action={action}, total_refund={total_ref}"
        db.add(AuditLog(action="return_create", actor_user_id=current_user.id, result="success", detail=detail))
    except Exception:
        # No bloquear por error de auditoría
        pass

    return db_return


@router.get("/{return_id}", response_model=ReturnSchema)
async def get_return(
    return_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = await db.execute(select(ReturnModel).where(ReturnModel.id == return_id))
    ret = res.scalar_one_or_none()
    if not ret:
        raise HTTPException(status_code=404, detail="Devolución no encontrada")
    return ret


@router.get("/", response_model=ReturnList)
async def list_returns(
    skip: int = 0,
    limit: int = 50,
    sale_id: int | None = Query(None),
    date_from: str | None = Query(None, description="YYYY-MM-DD o ISO datetime"),
    date_to: str | None = Query(None, description="YYYY-MM-DD o ISO datetime"),
    action: str | None = Query(None, description="refund|credit_note|exchange"),
    refund_method: str | None = Query(None),
    status_param: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    start_dt, end_dt = _parse_date_range(date_from, date_to)
    filters = []
    if sale_id is not None:
        filters.append(ReturnModel.sale_id == sale_id)
    if start_dt is not None:
        filters.append(ReturnModel.created_at >= start_dt)
    if end_dt is not None:
        filters.append(ReturnModel.created_at <= end_dt)
    if action:
        filters.append(ReturnModel.action == action)
    if refund_method:
        filters.append(ReturnModel.refund_method == refund_method)
    if status_param:
        filters.append(ReturnModel.status == status_param)

    # total count
    total_result = await db.execute(select(func.count()).select_from(ReturnModel).where(*filters))
    total = int(total_result.scalar() or 0)

    stmt = (
        select(ReturnModel)
        .where(*filters)
        .order_by(ReturnModel.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    res = await db.execute(stmt)
    items = res.scalars().all()
    return {"items": items, "total": total}


@router.get("/export")
async def export_returns_csv(
    sale_id: int | None = Query(None),
    date_from: str | None = Query(None, description="YYYY-MM-DD o ISO datetime"),
    date_to: str | None = Query(None, description="YYYY-MM-DD o ISO datetime"),
    action: str | None = Query(None),
    refund_method: str | None = Query(None),
    status_param: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    start_dt, end_dt = _parse_date_range(date_from, date_to)
    filters = []
    if sale_id is not None:
        filters.append(ReturnModel.sale_id == sale_id)
    if start_dt is not None:
        filters.append(ReturnModel.created_at >= start_dt)
    if end_dt is not None:
        filters.append(ReturnModel.created_at <= end_dt)
    if action:
        filters.append(ReturnModel.action == action)
    if refund_method:
        filters.append(ReturnModel.refund_method == refund_method)
    if status_param:
        filters.append(ReturnModel.status == status_param)

    res = await db.execute(select(ReturnModel).where(*filters).order_by(ReturnModel.created_at.desc()))
    items = res.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'id', 'sale_id', 'created_at', 'action', 'refund_method', 'subtotal_refund', 'tax_refund', 'total_refund', 'status', 'items_returned_count'
    ])
    for r in items:
        items_count = 0
        try:
            for it in (r.items_returned or []):
                if isinstance(it, dict):
                    items_count += int(it.get('quantity') or 0)
        except Exception:
            pass
        writer.writerow([
            r.id,
            r.sale_id,
            r.created_at.isoformat() if getattr(r, 'created_at', None) else '',
            r.action,
            r.refund_method or '',
            f"{r.subtotal_refund:.2f}",
            f"{r.tax_refund:.2f}",
            f"{r.total_refund:.2f}",
            r.status,
            items_count,
        ])

    output.seek(0)
    filename = f"returns_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue().encode('utf-8-sig')]),
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )
