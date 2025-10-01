"""
Endpoints de ventas
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from db.session import get_db
from models.sale import Sale
from models.product import Product
from schemas.sale import Sale as SaleSchema, SaleCreate, SaleUpdate, SaleList

router = APIRouter()


@router.get("/", response_model=SaleList)
def get_sales(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Obtener lista de ventas"""
    total = db.query(Sale).count()
    sales = db.query(Sale).offset(skip).limit(limit).all()
    
    return {"items": sales, "total": total}


@router.get("/{sale_id}", response_model=SaleSchema)
def get_sale(sale_id: int, db: Session = Depends(get_db)):
    """Obtener una venta por ID"""
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venta no encontrada"
        )
    
    return sale


@router.post("/", response_model=SaleSchema, status_code=status.HTTP_201_CREATED)
def create_sale(sale: SaleCreate, db: Session = Depends(get_db)):
    """Crear una nueva venta"""
    # TODO: Obtener user_id del token de autenticación
    user_id = 1  # Por ahora hardcodeado
    
    # Verificar stock de productos
    for item in sale.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto {item.product_id} no encontrado"
            )
        
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente para {product.name}"
            )
    
    # Crear venta
    sale_data = sale.model_dump()
    sale_data["user_id"] = user_id
    
    db_sale = Sale(**sale_data)
    db.add(db_sale)
    
    # Actualizar stock de productos
    for item in sale.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        product.stock -= item.quantity
    
    db.commit()
    db.refresh(db_sale)
    
    return db_sale


@router.put("/{sale_id}", response_model=SaleSchema)
def update_sale(
    sale_id: int,
    sale: SaleUpdate,
    db: Session = Depends(get_db)
):
    """Actualizar una venta (principalmente el estado)"""
    db_sale = db.query(Sale).filter(Sale.id == sale_id).first()
    
    if not db_sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venta no encontrada"
        )
    
    # Actualizar campos
    update_data = sale.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_sale, field, value)
    
    db.commit()
    db.refresh(db_sale)
    
    return db_sale
