"""
Modelo de Alerta de Inventario
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.session import Base


class InventoryAlert(Base):
    __tablename__ = "inventory_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    alert_type = Column(String(50), nullable=False, index=True)  # low_stock, no_stock, no_movement, restock_suggestion
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    message = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_read = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Información adicional
    current_stock = Column(Integer, nullable=True)
    threshold = Column(Integer, nullable=True)
    days_without_movement = Column(Integer, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relación con producto
    product = relationship("Product", backref="alerts")
