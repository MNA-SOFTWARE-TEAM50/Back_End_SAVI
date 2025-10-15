"""
Modelo de Devolución
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.sql import func
from db.session import Base


class Return(Base):
    __tablename__ = "returns"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    user_id = Column(CHAR(36), ForeignKey("users.id"), nullable=False)

    # Items involucrados
    items_returned = Column(JSON, nullable=False)  # lista de {product_id, product_name, quantity, unit_price, subtotal}
    items_exchanged = Column(JSON, nullable=True)  # opcional para cambios

    # Totales de reembolso/cambio
    subtotal_refund = Column(Float, default=0.0, nullable=False)
    tax_refund = Column(Float, default=0.0, nullable=False)
    total_refund = Column(Float, default=0.0, nullable=False)

    action = Column(String(20), nullable=False)  # refund | credit_note | exchange
    refund_method = Column(String(20), nullable=True)  # cash | card | transfer (si aplica)

    reason = Column(String(120), nullable=True)
    status = Column(String(20), default="completed", nullable=False)  # pending | approved | rejected | completed | failed

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
