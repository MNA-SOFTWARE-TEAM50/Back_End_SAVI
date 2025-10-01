"""
Schemas de Usuario con Pydantic
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """Base de usuario"""
    username: str
    email: EmailStr
    full_name: str
    role: str = "cashier"


class UserCreate(UserBase):
    """Schema para crear usuario"""
    password: str


class UserUpdate(BaseModel):
    """Schema para actualizar usuario"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """Usuario en base de datos"""
    id: str  # UUID4 como string
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class User(UserInDB):
    """Usuario para respuesta API (sin contraseña)"""
    pass


class Token(BaseModel):
    """Token de acceso"""
    access_token: str
    token_type: str = "bearer"


class UserLoginResponse(BaseModel):
    """Respuesta del login"""
    id: str
    username: str
    email: str
    full_name: str
    role: str


class LoginResponse(BaseModel):
    """Respuesta completa del login"""
    access_token: str
    token_type: str = "bearer"
    message: str
    user: UserLoginResponse


class TokenData(BaseModel):
    """Datos del token"""
    username: Optional[str] = None
