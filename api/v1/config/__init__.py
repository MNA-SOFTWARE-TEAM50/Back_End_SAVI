"""
Módulo de configuración v1
"""
from fastapi import APIRouter
from . import users

router = APIRouter()

# Subrutas de configuración
router.include_router(users.router, prefix="/users", tags=["Usuarios"])
