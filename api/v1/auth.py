"""
Endpoints de autenticación
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.session import get_db
from models.user import User
from schemas.user import User as UserSchema, UserCreate, Token
from core.security import verify_password, get_password_hash, create_access_token, validate_password_policy, get_permissions_for_role
from models.audit_log import AuditLog
from datetime import datetime, timedelta

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Registrar un nuevo usuario"""
    # Verificar si el usuario ya existe
    result = await db.execute(select(User).filter(User.username == user.username))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identificador en uso"
        )
    
    result = await db.execute(select(User).filter(User.email == user.email))
    existing_email = result.scalar_one_or_none()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identificador en uso"
        )

    # Validar política de contraseña
    unmet = validate_password_policy(user.password)
    if unmet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña no cumple la política: " + "; ".join(unmet)
        )
    
    # Crear usuario
    user_data = user.model_dump()
    user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
    
    db_user = User(**user_data)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user


LOCK_WINDOW_MINUTES = 10
MAX_FAILED_ATTEMPTS = 5


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """Iniciar sesión - Autenticación de empleado"""
    # Buscar usuario
    result = await db.execute(select(User).filter(User.username == form_data.username))
    user = result.scalar_one_or_none()
    
    # Si no existe usuario
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Denegar acceso si inactivo/bloqueado con mensaje genérico
    if not user.is_active or getattr(user, "is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Lockout: 5 intentos fallidos en 10 minutos bloquean la cuenta
    now = datetime.utcnow()
    if getattr(user, "first_failed_at", None) and now - user.first_failed_at > timedelta(minutes=LOCK_WINDOW_MINUTES):
        user.failed_attempts = 0
        user.first_failed_at = None

    if not verify_password(form_data.password, user.hashed_password):
        if user.failed_attempts == 0:
            user.first_failed_at = now
        user.failed_attempts += 1

        if user.failed_attempts >= MAX_FAILED_ATTEMPTS and user.first_failed_at and now - user.first_failed_at <= timedelta(minutes=LOCK_WINDOW_MINUTES):
            user.is_locked = True
            user.locked_at = now
            # Auditoría de bloqueo
            audit = AuditLog(
                action="lock_user",
                actor_user_id=user.id,
                target_user_id=user.id,
                role_assigned=user.role,
                result="failure",
                detail="Cuenta bloqueada por intentos fallidos"
            )
            db.add(audit)

        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Éxito: resetear contadores de lockout
    user.failed_attempts = 0
    user.first_failed_at = None
    await db.commit()

    # Crear token, permisos y auditoría de login
    access_token = create_access_token(data={"sub": user.id, "username": user.username, "role": user.role})
    permissions = get_permissions_for_role(user.role)

    audit = AuditLog(
        action="login",
        actor_user_id=user.id,
        target_user_id=user.id,
        role_assigned=user.role,
        result="success",
        detail="Login exitoso"
    )
    db.add(audit)
    await db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "message": "Sesión iniciada",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "permissions": permissions
        }
    }


@router.get("/me", response_model=UserSchema)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Obtener usuario actual"""
    from core.security import decode_access_token
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")  # Ahora "sub" contiene el UUID
    token_iat = payload.get("iat")
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Si hubo logout después de emitido el token, invalidar
    if getattr(user, "last_logout_at", None) and token_iat:
        # token_iat puede venir como string/datetime; jose suele serializar datetime -> int timestamp
        try:
            iat_dt = datetime.utcfromtimestamp(token_iat) if isinstance(token_iat, (int, float)) else datetime.fromisoformat(token_iat)
            if user.last_logout_at and iat_dt < user.last_logout_at:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except Exception:
            # Si no podemos parsear, mejor invalidar por seguridad
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return user


@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Cerrar sesión: invalida el token actual registrando last_logout_at y audit log"""
    from core.security import decode_access_token

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    user.last_logout_at = datetime.utcnow()
    audit = AuditLog(
        action="logout",
        actor_user_id=user.id,
        target_user_id=user.id,
        role_assigned=user.role,
        result="success",
        detail="Logout manual"
    )
    db.add(audit)
    await db.commit()

    return {"message": "Sesión cerrada"}
