"""
Schemas de Producto con Pydantic
"""
from pydantic import BaseModel
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
