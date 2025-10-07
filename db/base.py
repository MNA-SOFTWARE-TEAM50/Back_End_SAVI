"""
Base de datos - Importar todos los modelos aquí
"""
from db.session import Base

# Importar todos los modelos para que SQLAlchemy los reconozca
from models.product import Product
from models.sale import Sale
from models.customer import Customer
from models.user import User

__all__ = ["Base"]
