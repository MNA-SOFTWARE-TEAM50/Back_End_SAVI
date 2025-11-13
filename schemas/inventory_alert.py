"""
Schemas para Alertas de Inventario
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class InventoryAlertBase(BaseModel):
    product_id: int
    alert_type: str = Field(..., description="Tipo de alerta: low_stock, no_stock, no_movement, restock_suggestion")
    severity: str = Field(..., description="Severidad: low, medium, high, critical")
    message: str
    current_stock: Optional[int] = None
    threshold: Optional[int] = None
    days_without_movement: Optional[int] = None


class InventoryAlertCreate(InventoryAlertBase):
    pass


class InventoryAlertUpdate(BaseModel):
    is_read: Optional[bool] = None
    is_active: Optional[bool] = None


class InventoryAlert(InventoryAlertBase):
    id: int
    is_active: bool
    is_read: bool
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class InventoryAlertWithProduct(InventoryAlert):
    product_name: str
    product_sku: Optional[str] = None
    product_category: str
    
    class Config:
        from_attributes = True


class AlertStats(BaseModel):
    total_alerts: int
    active_alerts: int
    unread_alerts: int
    critical_alerts: int
    by_type: dict
    by_severity: dict


class AlertConfig(BaseModel):
    low_stock_threshold: int = Field(default=10, description="Stock mínimo antes de alerta")
    critical_stock_threshold: int = Field(default=5, description="Stock crítico")
    no_movement_days: int = Field(default=30, description="Días sin movimiento para alerta")
    auto_generate_alerts: bool = Field(default=True, description="Generar alertas automáticamente")
