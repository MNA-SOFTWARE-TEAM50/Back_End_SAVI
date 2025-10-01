"""
Schemas de Cliente con Pydantic
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class CustomerBase(BaseModel):
    """Base de cliente"""
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class CustomerCreate(CustomerBase):
    """Schema para crear cliente"""
    pass


class CustomerUpdate(BaseModel):
    """Schema para actualizar cliente"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class Customer(CustomerBase):
    """Cliente para respuesta API"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CustomerList(BaseModel):
    """Lista de clientes"""
    items: list[Customer]
    total: int
