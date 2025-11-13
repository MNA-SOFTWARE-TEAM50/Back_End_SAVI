"""
Endpoints para Alertas de Inventario
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import joinedload
from typing import List, Optional
from datetime import datetime, timedelta

from db.session import get_db
from models.inventory_alert import InventoryAlert
from models.product import Product
from models.sale import Sale
from schemas.inventory_alert import (
    InventoryAlert as InventoryAlertSchema,
    InventoryAlertCreate,
    InventoryAlertUpdate,
    InventoryAlertWithProduct,
    AlertStats,
    AlertConfig
)
from core.security import get_current_user
from models.user import User

router = APIRouter()


@router.get("/stats", response_model=AlertStats)
async def get_alert_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener estadísticas de alertas de inventario
    """
    # Total de alertas
    total_result = await db.execute(select(func.count(InventoryAlert.id)))
    total_alerts = total_result.scalar() or 0
    
    # Alertas activas
    active_result = await db.execute(
        select(func.count(InventoryAlert.id)).where(InventoryAlert.is_active == True)
    )
    active_alerts = active_result.scalar() or 0
    
    # Alertas no leídas
    unread_result = await db.execute(
        select(func.count(InventoryAlert.id)).where(
            and_(InventoryAlert.is_active == True, InventoryAlert.is_read == False)
        )
    )
    unread_alerts = unread_result.scalar() or 0
    
    # Alertas críticas
    critical_result = await db.execute(
        select(func.count(InventoryAlert.id)).where(
            and_(InventoryAlert.is_active == True, InventoryAlert.severity == 'critical')
        )
    )
    critical_alerts = critical_result.scalar() or 0
    
    # Por tipo
    by_type_result = await db.execute(
        select(InventoryAlert.alert_type, func.count(InventoryAlert.id))
        .where(InventoryAlert.is_active == True)
        .group_by(InventoryAlert.alert_type)
    )
    by_type = {row[0]: row[1] for row in by_type_result.all()}
    
    # Por severidad
    by_severity_result = await db.execute(
        select(InventoryAlert.severity, func.count(InventoryAlert.id))
        .where(InventoryAlert.is_active == True)
        .group_by(InventoryAlert.severity)
    )
    by_severity = {row[0]: row[1] for row in by_severity_result.all()}
    
    return AlertStats(
        total_alerts=total_alerts,
        active_alerts=active_alerts,
        unread_alerts=unread_alerts,
        critical_alerts=critical_alerts,
        by_type=by_type,
        by_severity=by_severity
    )


@router.get("/", response_model=List[InventoryAlertWithProduct])
async def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    active_only: bool = Query(True, description="Solo alertas activas"),
    unread_only: bool = Query(False, description="Solo alertas no leídas"),
    alert_type: Optional[str] = Query(None, description="Filtrar por tipo de alerta"),
    severity: Optional[str] = Query(None, description="Filtrar por severidad"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener lista de alertas de inventario con información del producto
    """
    # Construir query base
    query = select(InventoryAlert).options(joinedload(InventoryAlert.product))
    
    # Aplicar filtros
    conditions = []
    if active_only:
        conditions.append(InventoryAlert.is_active == True)
    if unread_only:
        conditions.append(InventoryAlert.is_read == False)
    if alert_type:
        conditions.append(InventoryAlert.alert_type == alert_type)
    if severity:
        conditions.append(InventoryAlert.severity == severity)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # Ordenar por severidad y fecha
    severity_order = case(
        (InventoryAlert.severity == 'critical', 1),
        (InventoryAlert.severity == 'high', 2),
        (InventoryAlert.severity == 'medium', 3),
        (InventoryAlert.severity == 'low', 4),
        else_=5
    )
    query = query.order_by(severity_order, InventoryAlert.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    alerts = result.unique().scalars().all()
    
    # Transformar a schema con información del producto
    alerts_with_product = []
    for alert in alerts:
        alert_dict = {
            "id": alert.id,
            "product_id": alert.product_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
            "is_active": alert.is_active,
            "is_read": alert.is_read,
            "resolved_at": alert.resolved_at,
            "current_stock": alert.current_stock,
            "threshold": alert.threshold,
            "days_without_movement": alert.days_without_movement,
            "created_at": alert.created_at,
            "updated_at": alert.updated_at,
            "product_name": alert.product.name,
            "product_sku": alert.product.sku,
            "product_category": alert.product.category
        }
        alerts_with_product.append(InventoryAlertWithProduct(**alert_dict))
    
    return alerts_with_product


@router.get("/{alert_id}", response_model=InventoryAlertWithProduct)
async def get_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtener detalles de una alerta específica
    """
    result = await db.execute(
        select(InventoryAlert)
        .options(joinedload(InventoryAlert.product))
        .where(InventoryAlert.id == alert_id)
    )
    alert = result.unique().scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    return InventoryAlertWithProduct(
        id=alert.id,
        product_id=alert.product_id,
        alert_type=alert.alert_type,
        severity=alert.severity,
        message=alert.message,
        is_active=alert.is_active,
        is_read=alert.is_read,
        resolved_at=alert.resolved_at,
        current_stock=alert.current_stock,
        threshold=alert.threshold,
        days_without_movement=alert.days_without_movement,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
        product_name=alert.product.name,
        product_sku=alert.product.sku,
        product_category=alert.product.category
    )


@router.patch("/{alert_id}", response_model=InventoryAlertSchema)
async def update_alert(
    alert_id: int,
    alert_update: InventoryAlertUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Actualizar estado de una alerta (marcar como leída, desactivar, etc.)
    """
    result = await db.execute(
        select(InventoryAlert).where(InventoryAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    # Actualizar campos
    if alert_update.is_read is not None:
        alert.is_read = alert_update.is_read
    
    if alert_update.is_active is not None:
        alert.is_active = alert_update.is_active
        if not alert_update.is_active:
            alert.resolved_at = datetime.now()
    
    await db.commit()
    await db.refresh(alert)
    
    return alert


@router.post("/{alert_id}/mark-read")
async def mark_alert_as_read(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Marcar una alerta como leída
    """
    result = await db.execute(
        select(InventoryAlert).where(InventoryAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    alert.is_read = True
    await db.commit()
    
    return {"message": "Alerta marcada como leída", "alert_id": alert_id}


@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Resolver una alerta (marcarla como inactiva)
    """
    result = await db.execute(
        select(InventoryAlert).where(InventoryAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    alert.is_active = False
    alert.is_read = True
    alert.resolved_at = datetime.now()
    await db.commit()
    
    return {"message": "Alerta resuelta", "alert_id": alert_id}


@router.post("/mark-all-read")
async def mark_all_as_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Marcar todas las alertas activas como leídas
    """
    result = await db.execute(
        select(InventoryAlert).where(
            and_(InventoryAlert.is_active == True, InventoryAlert.is_read == False)
        )
    )
    alerts = result.scalars().all()
    
    for alert in alerts:
        alert.is_read = True
    
    await db.commit()
    
    return {"message": f"{len(alerts)} alertas marcadas como leídas"}


@router.post("/generate")
async def generate_alerts(
    config: AlertConfig = AlertConfig(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generar alertas automáticas basadas en el inventario actual
    Requiere rol de admin o manager
    """
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para generar alertas")
    
    generated_alerts = []
    
    # Obtener todos los productos
    result = await db.execute(select(Product))
    products = result.scalars().all()
    
    for product in products:
        # Desactivar TODAS las alertas antiguas del producto (de cualquier tipo)
        old_alerts_result = await db.execute(
            select(InventoryAlert).where(
                and_(
                    InventoryAlert.product_id == product.id,
                    InventoryAlert.is_active == True
                )
            )
        )
        old_alerts = old_alerts_result.scalars().all()
        for old_alert in old_alerts:
            old_alert.is_active = False
            old_alert.resolved_at = datetime.now()
        
        # 1. Alerta de sin stock - SIEMPRE CREAR NUEVA
        if product.stock == 0:
            alert = InventoryAlert(
                product_id=product.id,
                alert_type="no_stock",
                severity="critical",
                message=f"El producto '{product.name}' está agotado. Se requiere reabastecimiento urgente.",
                current_stock=0,
                threshold=config.low_stock_threshold,
                is_active=True,
                is_read=False
            )
            db.add(alert)
            generated_alerts.append(f"Sin stock: {product.name}")
        
        # 2. Alerta de stock bajo crítico - SIEMPRE CREAR NUEVA
        elif product.stock <= config.critical_stock_threshold:
            alert = InventoryAlert(
                product_id=product.id,
                alert_type="low_stock",
                severity="critical",
                message=f"El producto '{product.name}' tiene stock crítico ({product.stock} unidades). Reabastecer inmediatamente.",
                current_stock=product.stock,
                threshold=config.critical_stock_threshold,
                is_active=True,
                is_read=False
            )
            db.add(alert)
            generated_alerts.append(f"Stock crítico: {product.name} ({product.stock})")
        
        # 3. Alerta de stock bajo - SIEMPRE CREAR NUEVA
        elif product.stock <= config.low_stock_threshold:
            alert = InventoryAlert(
                product_id=product.id,
                alert_type="low_stock",
                severity="high",
                message=f"El producto '{product.name}' tiene stock bajo ({product.stock} unidades). Considere reabastecer pronto.",
                current_stock=product.stock,
                threshold=config.low_stock_threshold,
                is_active=True,
                is_read=False
            )
            db.add(alert)
            generated_alerts.append(f"Stock bajo: {product.name} ({product.stock})")
        
        # 4. Alerta de productos sin movimiento
        # Verificar última venta del producto
        cutoff_date = datetime.now() - timedelta(days=config.no_movement_days)
        last_sale_result = await db.execute(
            select(Sale)
            .where(Sale.created_at >= cutoff_date)
            .where(Sale.items.contains(f'"product_id": {product.id}'))
            .order_by(Sale.created_at.desc())
            .limit(1)
        )
        last_sale = last_sale_result.scalar_one_or_none()
        
        if not last_sale and product.stock > 0:
            alert = InventoryAlert(
                product_id=product.id,
                alert_type="no_movement",
                severity="medium",
                message=f"El producto '{product.name}' no ha tenido ventas en los últimos {config.no_movement_days} días. Considere promociones o descuentos.",
                current_stock=product.stock,
                days_without_movement=config.no_movement_days,
                is_active=True,
                is_read=False
            )
            db.add(alert)
            generated_alerts.append(f"Sin movimiento: {product.name}")
    
    await db.commit()
    
    return {
        "message": f"Se generaron {len(generated_alerts)} alertas",
        "alerts": generated_alerts
    }


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Eliminar una alerta (solo admin)
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden eliminar alertas")
    
    result = await db.execute(
        select(InventoryAlert).where(InventoryAlert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    await db.delete(alert)
    await db.commit()
    
    return {"message": "Alerta eliminada", "alert_id": alert_id}
