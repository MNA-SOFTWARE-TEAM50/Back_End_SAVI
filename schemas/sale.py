"""
Schemas de Venta con Pydantic
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SaleItem(BaseModel):
    """Item de venta"""
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float


class SaleBase(BaseModel):
    """Base de venta"""
    items: List[SaleItem]
    subtotal: float
    tax: float
    discount: float = 0.0
    total: float
    payment_method: str  # cash, card, transfer
    customer_id: Optional[int] = None


class SaleCreate(SaleBase):
    """Schema para crear venta"""
    pass


class SaleUpdate(BaseModel):
    """Schema para actualizar venta"""
    status: Optional[str] = None  # pending, completed, cancelled


class Sale(SaleBase):
    """Venta para respuesta API"""
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SaleList(BaseModel):
    """Lista de ventas"""
    items: list[Sale]
    total: int


class SaleStats(BaseModel):
    """Estadísticas de ventas"""
    total_sales: int
    total_revenue: float
    average_sale: float
    sales_by_method: dict
