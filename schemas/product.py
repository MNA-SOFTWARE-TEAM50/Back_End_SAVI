"""
Schemas de Producto con Pydantic
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class ProductBase(BaseModel):
    """Base de producto"""
    name: str
    description: Optional[str] = None
    price: float
    stock: int = 0
    category: str
    sku: Optional[str] = None
    barcode: Optional[str] = None
    image_url: Optional[str] = None
    
    # Campos de promoción
    discount_percentage: float = Field(default=0.0, ge=0, le=100)
    has_promotion: bool = False
    promotion_start: Optional[datetime] = None
    promotion_end: Optional[datetime] = None
    promotion_description: Optional[str] = None


class ProductCreate(ProductBase):
    """Schema para crear producto"""
    pass


class ProductUpdate(BaseModel):
    """Schema para actualizar producto"""
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    image_url: Optional[str] = None
    
    # Campos de promoción
    discount_percentage: Optional[float] = Field(default=None, ge=0, le=100)
    has_promotion: Optional[bool] = None
    promotion_start: Optional[datetime] = None
    promotion_end: Optional[datetime] = None
    promotion_description: Optional[str] = None


class Product(ProductBase):
    """Producto para respuesta API"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ProductList(BaseModel):
    """Lista de productos"""
    items: list[Product]
    total: int
