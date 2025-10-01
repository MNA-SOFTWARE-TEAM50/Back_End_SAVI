"""
Modelo de Venta
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.session import Base


class Sale(Base):
    __tablename__ = "sales"
    
    id = Column(Integer, primary_key=True, index=True)
    items = Column(JSON, nullable=False)  # Lista de items vendidos
    subtotal = Column(Float, nullable=False)
    tax = Column(Float, nullable=False)
    discount = Column(Float, default=0.0)
    total = Column(Float, nullable=False)
    payment_method = Column(String(20), nullable=False)  # cash, card, transfer
    status = Column(String(20), default="completed", nullable=False)  # pending, completed, cancelled
    
    # Relaciones
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    user_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
