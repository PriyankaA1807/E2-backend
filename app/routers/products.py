from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas


router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


# --------------------------------------------------
# CREATE PRODUCT
# --------------------------------------------------

@router.post("/", response_model=schemas.ProductResponse)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db)
):
    existing_product = (
        db.query(models.Product)
        .filter(models.Product.sku == product.sku)
        .first()
    )

    if existing_product:
        raise HTTPException(
            status_code=400,
            detail="Product with this SKU already exists"
        )

    new_product = models.Product(
        sku=product.sku,
        name=product.name,
        category=product.category,
        unit_price=product.unit_price,
        reorder_level=product.reorder_level
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


# --------------------------------------------------
# GET ALL PRODUCTS
# --------------------------------------------------

@router.get("/", response_model=list[schemas.ProductResponse])
def get_products(
    db: Session = Depends(get_db)
):
    return db.query(models.Product).all()


# --------------------------------------------------
# GET PRODUCT BY ID
# --------------------------------------------------

@router.get("/{product_id}", response_model=schemas.ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = (
        db.query(models.Product)
        .filter(models.Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


# --------------------------------------------------
# DELETE PRODUCT
# --------------------------------------------------

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = (
        db.query(models.Product)
        .filter(models.Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db.delete(product)
    db.commit()

    return {
        "message": "Product deleted successfully"
    }
