"""
Endpoints de productos
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from db.session import get_db
from models.product import Product
from schemas.product import Product as ProductSchema, ProductCreate, ProductUpdate, ProductList

router = APIRouter()


@router.get("/", response_model=ProductList)
async def get_products(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Obtener lista de productos"""
    query = select(Product)
    
    if category:
        query = query.filter(Product.category == category)
    
    # Contar total
    count_query = select(func.count()).select_from(Product)
    if category:
        count_query = count_query.filter(Product.category == category)
    
    result = await db.execute(count_query)
    total = result.scalar()
    
    # Obtener productos
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    products = result.scalars().all()
    
    return {"items": products, "total": total}


@router.get("/{product_id}", response_model=ProductSchema)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Obtener un producto por ID"""
    result = await db.execute(select(Product).filter(Product.id == product_id))
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    
    return product


@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_db)):
    """Crear un nuevo producto"""
    # Verificar si el código de barras ya existe
    if product.barcode:
        result = await db.execute(select(Product).filter(Product.barcode == product.barcode))
        existing = result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código de barras ya existe"
            )
    
    db_product = Product(**product.model_dump())
    db.add(db_product)
    await db.flush()
    await db.refresh(db_product)
    
    return db_product


@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(
    product_id: int,
    product: ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Actualizar un producto"""
    result = await db.execute(select(Product).filter(Product.id == product_id))
    db_product = result.scalar_one_or_none()
    
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    
    # Actualizar campos
    update_data = product.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    await db.flush()
    await db.refresh(db_product)
    
    return db_product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Eliminar un producto"""
    result = await db.execute(select(Product).filter(Product.id == product_id))
    db_product = result.scalar_one_or_none()
    
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    
    await db.delete(db_product)
    
    return None
