"""
Router principal de la API v1
"""
from fastapi import APIRouter
from api.v1 import products, sales, customers, auth, config, imports, returns, inventory_alerts

api_router = APIRouter()

# Incluir routers
api_router.include_router(auth.router, prefix="/auth", tags=["Autenticación"])
api_router.include_router(products.router, prefix="/products", tags=["Productos"])
api_router.include_router(sales.router, prefix="/sales", tags=["Ventas"])
api_router.include_router(customers.router, prefix="/customers", tags=["Clientes"])
api_router.include_router(config.router, prefix="/config", tags=["Configuración"])
api_router.include_router(imports.router, prefix="/imports", tags=["Imports"])
api_router.include_router(returns.router, prefix="/returns", tags=["Devoluciones"])
api_router.include_router(inventory_alerts.router, prefix="/inventory-alerts", tags=["Alertas de Inventario"])
