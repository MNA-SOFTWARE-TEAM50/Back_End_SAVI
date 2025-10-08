"""
Usuarios - CRUD para gestión de usuarios (Configuración)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from db.session import get_db
from models.user import User
from schemas.user import (
    User as UserSchema,
    UserCreate,
    UserUpdate,
    UserList,
)
from core.security import get_password_hash, decode_access_token, validate_password_policy
from models.audit_log import AuditLog

router = APIRouter()

# Esquema OAuth2 para extraer el token del encabezado Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Obtiene el usuario actual desde el token JWT."""
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
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Usuario inactivo")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Exige que el usuario tenga rol admin."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido a administradores")
    return current_user


@router.get("/", response_model=UserList, dependencies=[Depends(require_admin)])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    q: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """Listar usuarios con paginación y filtros básicos"""
    query = select(User)
    count_query = select(func.count()).select_from(User)

    if q:
        like = f"%{q}%"
        query = query.filter((User.username.ilike(like)) | (User.full_name.ilike(like)) | (User.email.ilike(like)))
        count_query = count_query.filter((User.username.ilike(like)) | (User.full_name.ilike(like)) | (User.email.ilike(like)))

    if role:
        query = query.filter(User.role == role)
        count_query = count_query.filter(User.role == role)

    if is_active is not None:
        query = query.filter(User.is_active == is_active)
        count_query = count_query.filter(User.is_active == is_active)

    result = await db.execute(count_query)
    total = result.scalar() or 0

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    items = result.scalars().all()

    return {"items": items, "total": total}


@router.get("/{user_id}", response_model=UserSchema, dependencies=[Depends(require_admin)])
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """Obtener un usuario por su UUID"""
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return user


@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Crear un nuevo usuario"""
    # Unicidad de username y email
    result = await db.execute(select(User).filter(User.username == payload.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Identificador en uso")

    result = await db.execute(select(User).filter(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Identificador en uso")

    # Validar política de contraseña
    unmet = validate_password_policy(payload.password)
    if unmet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña no cumple la política: " + "; ".join(unmet)
        )

    data = payload.model_dump()
    data["hashed_password"] = get_password_hash(data.pop("password"))

    user = User(**data)
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Bitácora de auditoría (alta de usuario)
    audit = AuditLog(
        action="create_user",
        actor_user_id=current_user.id,
        target_user_id=user.id,
        role_assigned=user.role,
        result="success",
        detail=f"Alta de usuario {user.username}"
    )
    db.add(audit)
    await db.commit()

    return user


@router.put("/{user_id}", response_model=UserSchema)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Actualizar datos de un usuario; si viene password, se re-hashea"""
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    update_data = payload.model_dump(exclude_unset=True)

    # Validar email/username si cambian
    if "email" in update_data and update_data["email"] != user.email:
        result = await db.execute(select(User).filter(User.email == update_data["email"]))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Identificador en uso")

    if "username" in update_data and update_data["username"] != user.username:
        result = await db.execute(select(User).filter(User.username == update_data["username"]))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Identificador en uso")

    # Manejar cambio de contraseña si se envía "password"
    password = update_data.pop("password", None)
    if password:
        unmet = validate_password_policy(password)
        if unmet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La contraseña no cumple la política: " + "; ".join(unmet)
            )
        user.hashed_password = get_password_hash(password)

    for k, v in update_data.items():
        setattr(user, k, v)

    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
async def delete_user(user_id: str, soft: bool = True, db: AsyncSession = Depends(get_db)):
    """Eliminar usuario. Por defecto soft delete via is_active=False; hard delete con soft=False"""
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    if soft:
        user.is_active = False
        await db.commit()
        return None

    await db.delete(user)
    await db.commit()
    return None
