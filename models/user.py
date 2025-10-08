"""
Modelo de Usuario
"""
from sqlalchemy import Boolean, Column, String, DateTime, Integer
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.sql import func
from db.session import Base
import uuid


class User(Base):
    __tablename__ = "users"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="cashier", nullable=False)  # admin, cashier, manager
    is_active = Column(Boolean, default=True)
    # Seguridad de autenticación
    failed_attempts = Column(Integer, default=0, nullable=False)
    first_failed_at = Column(DateTime(timezone=True), nullable=True)
    is_locked = Column(Boolean, default=False, nullable=False)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    last_logout_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
