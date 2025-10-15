"""
Endpoints de ventas
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from datetime import datetime, date, time
import csv
import io
from fastapi.responses import StreamingResponse

from db.session import get_db
from models.sale import Sale
from models.product import Product
from models.user import User
from schemas.sale import Sale as SaleSchema, SaleCreate, SaleUpdate, SaleList, TodayStats, TopProducts, TopProduct
from models.returns import Return as ReturnModel
from core.security import get_current_user

router = APIRouter()


def _parse_date_range(date_from: str | None, date_to: str | None):
    start_dt = None
    end_dt = None
    try:
        if date_from:
            # Accept YYYY-MM-DD or ISO datetime
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
        # Ignore parsing errors; leave None
        pass
    return start_dt, end_dt


@router.get("/", response_model=SaleList)
async def get_sales(
    skip: int = 0,
    limit: int = 100,
    date_from: str | None = Query(None, description="YYYY-MM-DD o ISO datetime"),
    date_to: str | None = Query(None, description="YYYY-MM-DD o ISO datetime"),
    sale_id: int | None = Query(None, description="Filtrar por ID de venta"),
    payment_method: str | None = None,
    status_param: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener lista de ventas"""
    filters = []
    start_dt, end_dt = _parse_date_range(date_from, date_to)
    if start_dt is not None:
        filters.append(Sale.created_at >= start_dt)
    if end_dt is not None:
        filters.append(Sale.created_at <= end_dt)
    if payment_method:
        filters.append(Sale.payment_method == payment_method)
    if status_param:
        filters.append(Sale.status == status_param)
    if sale_id is not None:
        filters.append(Sale.id == sale_id)

    # total count
    total_result = await db.execute(select(func.count()).select_from(Sale).where(*filters))
    total = int(total_result.scalar() or 0)

    result = await db.execute(
        select(Sale)
        .where(*filters)
        .order_by(Sale.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    sales = result.scalars().all()
    # Compute net_total per sale (total - sum(total_refund) for completed returns)
    items_with_net = []
    for s in sales:
        ret_res = await db.execute(select(func.coalesce(func.sum(ReturnModel.total_refund), 0.0)).where(ReturnModel.sale_id == s.id, ReturnModel.status == 'completed'))
        total_ref = float(ret_res.scalar() or 0.0)
        # attach dynamic attribute for serialization via from_attributes
        setattr(s, 'net_total', float(s.total) - total_ref)
        items_with_net.append(s)
    
    return {"items": items_with_net, "total": total}



@router.post("/", response_model=SaleSchema, status_code=status.HTTP_201_CREATED)
async def create_sale(
    sale: SaleCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crear una nueva venta y descontar del inventario"""
    # Verificar stock de productos y recopilar productos
    products_to_update = []
    for item in sale.items:
        result = await db.execute(select(Product).filter(Product.id == item.product_id))
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto {item.product_id} no encontrado"
            )
        
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente para {product.name}. Disponible: {product.stock}, Solicitado: {item.quantity}"
            )
        
        products_to_update.append((product, item.quantity))
    
    # Crear venta
    sale_data = sale.model_dump()
    # Convertir items a dict para JSON
    sale_data["items"] = [item.model_dump() for item in sale.items]
    sale_data["user_id"] = current_user.id
    sale_data["customer_id"] = None  # Customers deprecated
    
    db_sale = Sale(**sale_data)
    db.add(db_sale)
    
    # Actualizar stock de productos
    for product, quantity in products_to_update:
        product.stock -= quantity
    
    await db.flush()
    await db.refresh(db_sale)
    
    return db_sale


@router.get("/stats/today", response_model=TodayStats)
async def get_today_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """KPIs de hoy: ingresos totales, productos vendidos y clientes atendidos (distintos)."""
    # Determinar el inicio del día en la zona del servidor (asumimos UTC o tz de DB)
    # Usamos DATE(created_at) = CURRENT_DATE para MySQL
    # Obtener todas las ventas de hoy
    result = await db.execute(
        select(Sale).where(func.date(Sale.created_at) == func.current_date())
    )
    sales_today = result.scalars().all()

    # Calculate revenue using net totals (subtracting refunds)
    revenue_today = 0.0
    if sales_today:
        for s in sales_today:
            ret_res = await db.execute(select(func.coalesce(func.sum(ReturnModel.total_refund), 0.0)).where(ReturnModel.sale_id == s.id, ReturnModel.status == 'completed'))
            total_ref = float(ret_res.scalar() or 0.0)
            revenue_today += float(s.total) - total_ref
    # Contar productos vendidos sumando quantities en items JSON
    products_sold_today = 0
    customers_set = set()
    for s in sales_today:
        try:
            items = s.items or []
            for it in items:
                # it puede ser dict con 'quantity'
                qty = it.get('quantity', 0) if isinstance(it, dict) else 0
                products_sold_today += int(qty or 0)
        except Exception:
            # Si items no es iterable, ignorar
            pass
        if s.customer_id:
            customers_set.add(s.customer_id)

    # Si no hay customer_id registrados (funcionalidad de clientes desactivada), usamos # de tickets
    customers_today = len(customers_set) if len(customers_set) > 0 else len(sales_today)

    return TodayStats(
        revenue_today=revenue_today,
        products_sold_today=products_sold_today,
        customers_today=customers_today,
        transactions_today=len(sales_today),
    )


@router.get("/stats", response_model=TodayStats)
async def get_stats(
    date_from: str | None = Query(None, description="YYYY-MM-DD o ISO datetime"),
    date_to: str | None = Query(None, description="YYYY-MM-DD o ISO datetime"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """KPIs por rango de fechas: ingresos, productos vendidos, clientes/transacciones."""
    start_dt, end_dt = _parse_date_range(date_from, date_to)
    filters = []
    if start_dt is not None:
        filters.append(Sale.created_at >= start_dt)
    if end_dt is not None:
        filters.append(Sale.created_at <= end_dt)

    result = await db.execute(select(Sale).where(*filters))
    sales = result.scalars().all()

    # Use net totals for revenue
    revenue = 0.0
    if sales:
        for s in sales:
            ret_res = await db.execute(select(func.coalesce(func.sum(ReturnModel.total_refund), 0.0)).where(ReturnModel.sale_id == s.id, ReturnModel.status == 'completed'))
            total_ref = float(ret_res.scalar() or 0.0)
            revenue += float(s.total) - total_ref
    products_sold = 0
    customers_set: set[int] = set()
    for s in sales:
        try:
            items = s.items or []
            for it in items:
                qty = it.get('quantity', 0) if isinstance(it, dict) else 0
                products_sold += int(qty or 0)
        except Exception:
            pass
        if s.customer_id:
            customers_set.add(s.customer_id)

    customers = len(customers_set) if len(customers_set) > 0 else len(sales)

    return TodayStats(
        revenue_today=revenue,
        products_sold_today=products_sold,
        customers_today=customers,
        transactions_today=len(sales),
    )


@router.get("/recent", response_model=SaleList)
async def get_recent_sales(
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Últimas ventas (por fecha desc)."""
    result = await db.execute(select(Sale).order_by(Sale.created_at.desc()).limit(limit))
    sales = result.scalars().all()
    # attach net_total
    items_with_net = []
    for s in sales:
        ret_res = await db.execute(select(func.coalesce(func.sum(ReturnModel.total_refund), 0.0)).where(ReturnModel.sale_id == s.id, ReturnModel.status == 'completed'))
        total_ref = float(ret_res.scalar() or 0.0)
        setattr(s, 'net_total', float(s.total) - total_ref)
        items_with_net.append(s)
    return {"items": items_with_net, "total": len(items_with_net)}


@router.get("/top-products", response_model=TopProducts)
async def get_top_products(
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    limit: int = 5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Top productos más vendidos (por cantidad) en el rango dado, basados en items JSON de ventas."""
    start_dt, end_dt = _parse_date_range(date_from, date_to)
    filters = []
    if start_dt is not None:
      filters.append(Sale.created_at >= start_dt)
    if end_dt is not None:
      filters.append(Sale.created_at <= end_dt)

    result = await db.execute(select(Sale).where(*filters))
    sales = result.scalars().all()

    agg: dict[str, dict] = {}
    for s in sales:
        items = s.items or []
        if not isinstance(items, list):
            continue
        for it in items:
            if not isinstance(it, dict):
                continue
            name = str(it.get('product_name') or 'Producto')
            pid = it.get('product_id')
            qty = int(it.get('quantity') or 0)
            subtotal = float(it.get('subtotal') or 0)
            key = f"{pid}:{name}"
            if key not in agg:
                agg[key] = { 'product_id': pid, 'product_name': name, 'total_quantity': 0, 'total_revenue': 0.0 }
            agg[key]['total_quantity'] += qty
            agg[key]['total_revenue'] += subtotal

    items = [TopProduct(product_id=v['product_id'], product_name=v['product_name'], total_quantity=v['total_quantity'], total_revenue=v['total_revenue']) for v in agg.values()]
    items.sort(key=lambda x: (-x.total_quantity, -x.total_revenue))
    return { 'items': items[:limit] }


@router.get("/export")
async def export_sales_csv(
    date_from: str | None = Query(None, description="YYYY-MM-DD o ISO datetime"),
    date_to: str | None = Query(None, description="YYYY-MM-DD o ISO datetime"),
    sale_id: int | None = Query(None, description="Filtrar por ID de venta"),
    payment_method: str | None = None,
    status_param: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Exporta ventas en CSV usando los mismos filtros del listado."""
    start_dt, end_dt = _parse_date_range(date_from, date_to)
    filters = []
    if start_dt is not None:
        filters.append(Sale.created_at >= start_dt)
    if end_dt is not None:
        filters.append(Sale.created_at <= end_dt)
    if payment_method:
        filters.append(Sale.payment_method == payment_method)
    if status_param:
        filters.append(Sale.status == status_param)
    if sale_id is not None:
        filters.append(Sale.id == sale_id)

    result = await db.execute(select(Sale).where(*filters).order_by(Sale.created_at.desc()))
    sales = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    # encabezados
    writer.writerow([
        'id', 'created_at', 'payment_method', 'status', 'subtotal', 'tax', 'discount', 'total', 'net_total', 'items_count'
    ])
    for s in sales:
        # compute net_total per sale for export
        ret_res = await db.execute(select(func.coalesce(func.sum(ReturnModel.total_refund), 0.0)).where(ReturnModel.sale_id == s.id, ReturnModel.status == 'completed'))
        total_ref = float(ret_res.scalar() or 0.0)
        net_total = float(s.total) - total_ref
        items = s.items or []
        items_count = 0
        try:
            for it in items:
                qty = it.get('quantity', 0) if isinstance(it, dict) else 0
                items_count += int(qty or 0)
        except Exception:
            pass
        writer.writerow([
            s.id,
            s.created_at.isoformat() if getattr(s, 'created_at', None) else '',
            s.payment_method,
            s.status,
            f"{s.subtotal:.2f}",
            f"{s.tax:.2f}",
            f"{s.discount:.2f}",
            f"{s.total:.2f}",
            f"{net_total:.2f}",
            items_count,
        ])

    output.seek(0)
    filename = f"sales_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        iter([output.getvalue().encode('utf-8-sig')]),
        media_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}"'}
    )


@router.get("/{sale_id}", response_model=SaleSchema)
async def get_sale(
    sale_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener una venta por ID"""
    result = await db.execute(select(Sale).filter(Sale.id == sale_id))
    sale = result.scalar_one_or_none()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venta no encontrada"
        )
    
    if sale:
        ret_res = await db.execute(select(func.coalesce(func.sum(ReturnModel.total_refund), 0.0)).where(ReturnModel.sale_id == sale.id, ReturnModel.status == 'completed'))
        total_ref = float(ret_res.scalar() or 0.0)
        setattr(sale, 'net_total', float(sale.total) - total_ref)
    return sale

@router.put("/{sale_id}", response_model=SaleSchema)
async def update_sale(
    sale_id: int,
    sale: SaleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualizar una venta (principalmente el estado)"""
    result = await db.execute(select(Sale).filter(Sale.id == sale_id))
    db_sale = result.scalar_one_or_none()
    
    if not db_sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venta no encontrada"
        )
    
    # Actualizar campos
    update_data = sale.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_sale, field, value)
    
    await db.flush()
    await db.refresh(db_sale)
    
    return db_sale
