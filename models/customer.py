"""
Modelo de Cliente
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from db.session import Base


class Customer(Base):
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    email = Column(String(100), unique=True, index=True)
    phone = Column(String(20))
    address = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
