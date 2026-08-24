from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Inventory, Product


router = APIRouter(
    prefix="/inventory",
    tags=["Inventory"]
)


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# GET all inventory
@router.get("/")
def get_inventory(db: Session = Depends(get_db)):
    inventory = db.query(Inventory).all()

    return inventory


# GET inventory for a specific product
@router.get("/{product_id}")
def get_product_inventory(
    product_id: int,
    db: Session = Depends(get_db)
):
    inventory = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id)
        .first()
    )

    if not inventory:
        raise HTTPException(
            status_code=404,
            detail="Inventory not found for this product"
        )

    return inventory


# POST create inventory
@router.post("/")
def create_inventory(
    product_id: int,
    current_stock: int = 0,
    reserved_stock: int = 0,
    db: Session = Depends(get_db)
):
    # Check whether product exists
    product = (
        db.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Check whether inventory already exists
    existing_inventory = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id)
        .first()
    )

    if existing_inventory:
        raise HTTPException(
            status_code=400,
            detail="Inventory already exists for this product"
        )

    inventory = Inventory(
        product_id=product_id,
        current_stock=current_stock,
        reserved_stock=reserved_stock
    )

    db.add(inventory)
    db.commit()
    db.refresh(inventory)

    return inventory


# PUT update inventory
@router.put("/{product_id}")
def update_inventory(
    product_id: int,
    current_stock: int,
    reserved_stock: int = 0,
    db: Session = Depends(get_db)
):
    inventory = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id)
        .first()
    )

    if not inventory:
        raise HTTPException(
            status_code=404,
            detail="Inventory not found for this product"
        )

    inventory.current_stock = current_stock
    inventory.reserved_stock = reserved_stock

    db.commit()
    db.refresh(inventory)

    return inventory