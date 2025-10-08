"""
Funciones de seguridad: autenticación, hashing, JWT
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from core.config import settings
import re

# Contexto para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña contra hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generar hash de contraseña"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crear token JWT
    
    Args:
        data: Datos a incluir en el token
        expires_delta: Tiempo de expiración
        
    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodificar token JWT
    
    Args:
        token: Token JWT a decodificar
        
    Returns:
        Payload del token o None si es inválido
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def validate_password_policy(password: str) -> list[str]:
    """Valida la política de contraseñas y regresa la lista de requisitos incumplidos."""
    unmet: list[str] = []
    if len(password) < 12:
        unmet.append("Debe tener al menos 12 caracteres")
    if not re.search(r"[A-Z]", password):
        unmet.append("Debe incluir al menos una letra mayúscula")
    if not re.search(r"[a-z]", password):
        unmet.append("Debe incluir al menos una letra minúscula")
    if not re.search(r"[0-9]", password):
        unmet.append("Debe incluir al menos un dígito")
    if not re.search(r"[^A-Za-z0-9]", password):
        unmet.append("Debe incluir al menos un símbolo")
    # No permitir 3 caracteres idénticos consecutivos
    if re.search(r"(.)\1\1", password):
        unmet.append("No debe contener 3 caracteres idénticos consecutivos")
    return unmet
