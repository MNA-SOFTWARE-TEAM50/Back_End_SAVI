"""
Endpoints de productos
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import os
from datetime import datetime

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
    # Verificar si el SKU ya existe
    if getattr(product, "sku", None):
        result = await db.execute(select(Product).filter(Product.sku == product.sku))
        existing_sku = result.scalar_one_or_none()
        if existing_sku:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SKU ya existe"
            )

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
    
    # Validaciones de unicidad si cambian sku o barcode
    update_data = product.model_dump(exclude_unset=True)
    if "sku" in update_data and update_data["sku"]:
        result = await db.execute(select(Product).filter(Product.sku == update_data["sku"]))
        existing_sku = result.scalar_one_or_none()
        if existing_sku and existing_sku.id != db_product.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SKU ya existe"
            )
    if "barcode" in update_data and update_data["barcode"]:
        result = await db.execute(select(Product).filter(Product.barcode == update_data["barcode"]))
        existing_barcode = result.scalar_one_or_none()
        if existing_barcode and existing_barcode.id != db_product.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Código de barras ya existe"
            )

    # Actualizar campos
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


@router.post("/{product_id}/image", response_model=ProductSchema)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Subir imagen para un producto y actualizar su image_url"""
    # Validar producto
    result = await db.execute(select(Product).filter(Product.id == product_id))
    db_product = result.scalar_one_or_none()
    if not db_product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Validar tipo de archivo
    allowed = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
    ext = allowed.get(file.content_type or "")
    if not ext:
        raise HTTPException(status_code=400, detail="Tipo de imagen no soportado. Usa JPG, PNG o WEBP")

    # Guardar archivo
    media_root = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'media')
    product_dir = os.path.join(media_root, 'products', str(product_id))
    os.makedirs(product_dir, exist_ok=True)
    fname = datetime.utcnow().strftime("%Y%m%d%H%M%S%f") + ext
    path = os.path.join(product_dir, fname)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # 5 MB
        raise HTTPException(status_code=400, detail="La imagen excede 5MB")
    with open(path, 'wb') as f:
        f.write(content)

    # Actualizar URL (ruta relativa servida por /media)
    rel_url = f"/media/products/{product_id}/{fname}"
    db_product.image_url = rel_url
    await db.flush()
    await db.refresh(db_product)
    return db_product
