"""
Inicializar todos los schemas
"""
from schemas.user import User, UserCreate, UserUpdate, Token, TokenData
from schemas.product import Product, ProductCreate, ProductUpdate, ProductList
from schemas.customer import Customer, CustomerCreate, CustomerUpdate, CustomerList
from schemas.sale import Sale, SaleCreate, SaleUpdate, SaleList, SaleItem, SaleStats

__all__ = [
    "User", "UserCreate", "UserUpdate", "Token", "TokenData",
    "Product", "ProductCreate", "ProductUpdate", "ProductList",
    "Customer", "CustomerCreate", "CustomerUpdate", "CustomerList",
    "Sale", "SaleCreate", "SaleUpdate", "SaleList", "SaleItem", "SaleStats"
]
