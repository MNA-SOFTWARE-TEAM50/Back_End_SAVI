"""
Funciones de seguridad: autenticación, hashing, JWT
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
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
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
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


# Mapa simple de permisos por rol (expandible en el futuro)
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "admin": [
        "users:read",
        "users:create",
        "users:update",
        "users:delete",
        "products:*",
        "sales:*",
        "customers:*",
        "config:*",
    ],
    "manager": [
        "products:*",
        "sales:read",
        "sales:create",
        "customers:*",
    ],
    "cashier": [
        "sales:read",
        "sales:create",
        "products:read",
        "customers:read",
    ],
}


def get_permissions_for_role(role: str) -> List[str]:
    return ROLE_PERMISSIONS.get(role, [])


# Dependency para obtener usuario actual desde token JWT
from fastapi import Depends, HTTPException, status as http_status
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependency para obtener el usuario actual desde el token JWT.
    Valida el token y verifica que no haya sido revocado por logout.
    
    Args:
        token: Token JWT del header Authorization
    """
    from db.session import get_db
    from models.user import User
    from sqlalchemy import select
    
    # Obtener sesión de base de datos
    async for db in get_db():
        break
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    token_iat = payload.get("iat")
    
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Validar revocación por logout
    if getattr(user, "last_logout_at", None) and token_iat:
        try:
            iat_dt = datetime.utcfromtimestamp(token_iat) if isinstance(token_iat, (int, float)) else datetime.fromisoformat(str(token_iat))
            if user.last_logout_at and iat_dt < user.last_logout_at:
                raise HTTPException(
                    status_code=http_status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido (sesión cerrada)",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=http_status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    return user
