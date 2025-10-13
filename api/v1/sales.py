"""
Endpoints de ventas
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from db.session import get_db
from models.sale import Sale
from models.product import Product
from models.user import User
from schemas.sale import Sale as SaleSchema, SaleCreate, SaleUpdate, SaleList
from core.security import get_current_user

router = APIRouter()


@router.get("/", response_model=SaleList)
async def get_sales(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener lista de ventas"""
    count_result = await db.execute(select(Sale))
    total = len(count_result.scalars().all())
    
    result = await db.execute(select(Sale).offset(skip).limit(limit).order_by(Sale.created_at.desc()))
    sales = result.scalars().all()
    
    return {"items": sales, "total": total}


@router.get("/{sale_id}", response_model=SaleSchema)
async def get_sale(
    sale_id: int, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtener una venta por ID"""
    result = await db.execute(select(Sale).filter(Sale.id == sale_id))
    sale = result.scalar_one_or_none()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venta no encontrada"
        )
    
    return sale


@router.post("/", response_model=SaleSchema, status_code=status.HTTP_201_CREATED)
async def create_sale(
    sale: SaleCreate, 
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Crear una nueva venta y descontar del inventario"""
    # Verificar stock de productos y recopilar productos
    products_to_update = []
    for item in sale.items:
        result = await db.execute(select(Product).filter(Product.id == item.product_id))
        product = result.scalar_one_or_none()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto {item.product_id} no encontrado"
            )
        
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente para {product.name}. Disponible: {product.stock}, Solicitado: {item.quantity}"
            )
        
        products_to_update.append((product, item.quantity))
    
    # Crear venta
    sale_data = sale.model_dump()
    # Convertir items a dict para JSON
    sale_data["items"] = [item.model_dump() for item in sale.items]
    sale_data["user_id"] = current_user.id
    sale_data["customer_id"] = None  # Customers deprecated
    
    db_sale = Sale(**sale_data)
    db.add(db_sale)
    
    # Actualizar stock de productos
    for product, quantity in products_to_update:
        product.stock -= quantity
    
    await db.flush()
    await db.refresh(db_sale)
    
    return db_sale


@router.put("/{sale_id}", response_model=SaleSchema)
async def update_sale(
    sale_id: int,
    sale: SaleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Actualizar una venta (principalmente el estado)"""
    result = await db.execute(select(Sale).filter(Sale.id == sale_id))
    db_sale = result.scalar_one_or_none()
    
    if not db_sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venta no encontrada"
        )
    
    # Actualizar campos
    update_data = sale.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_sale, field, value)
    
    await db.flush()
    await db.refresh(db_sale)
    
    return db_sale
