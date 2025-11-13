"""
Modelo de Producto
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func
from db.session import Base


class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(String(500))
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    sku = Column(String(50), unique=True, index=True, nullable=True)
    barcode = Column(String(50), unique=True, index=True)
    image_url = Column(String(500))
    
    # Campos de promoción y descuento
    discount_percentage = Column(Float, default=0.0, nullable=False)
    has_promotion = Column(Boolean, default=False, nullable=False)
    promotion_start = Column(DateTime(timezone=True), nullable=True)
    promotion_end = Column(DateTime(timezone=True), nullable=True)
    promotion_description = Column(String(500), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
