"""
Router principal de la API v1
"""
from fastapi import APIRouter
from api.v1 import products, sales, customers, auth

api_router = APIRouter()

# Incluir routers
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(products.router, prefix="/products", tags=["Productos"])
api_router.include_router(sales.router, prefix="/sales", tags=["Ventas"])
api_router.include_router(customers.router, prefix="/customers", tags=["Clientes"])
