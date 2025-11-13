"""
Inicializar todos los modelos
"""
from models.user import User
from models.product import Product
from models.customer import Customer
from models.sale import Sale
from models.returns import Return
from models.inventory_alert import InventoryAlert

__all__ = ["User", "Product", "Customer", "Sale", "Return", "InventoryAlert"]
