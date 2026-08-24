from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database import SessionLocal
from app.models import RestockOrder, Product, Supplier


router = APIRouter(
    prefix="/restock-orders",
    tags=["Restock Orders"]
)


# -----------------------------
# Database Dependency
# -----------------------------

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# -----------------------------
# Request Schema
# -----------------------------

class RestockOrderCreate(BaseModel):
    product_id: int
    supplier_id: int
    quantity: int
    status: str = "pending"
    expected_delivery: datetime | None = None


# -----------------------------
# Response Schema
# -----------------------------

class RestockOrderResponse(BaseModel):
    id: int
    product_id: int
    supplier_id: int
    quantity: int
    status: str
    order_date: datetime
    expected_delivery: datetime | None

    class Config:
        from_attributes = True


# -----------------------------
# Create Restock Order
# -----------------------------

@router.post("/", response_model=RestockOrderResponse)
def create_restock_order(
    order_data: RestockOrderCreate,
    db: Session = Depends(get_db)
):

    # Check Product
    product = db.query(Product).filter(
        Product.id == order_data.product_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # Check Supplier
    supplier = db.query(Supplier).filter(
        Supplier.id == order_data.supplier_id
    ).first()

    if not supplier:
        raise HTTPException(
            status_code=404,
            detail="Supplier not found"
        )

    # Validate quantity
    if order_data.quantity <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity must be greater than 0"
        )

    # Create order
    restock_order = RestockOrder(
        product_id=order_data.product_id,
        supplier_id=order_data.supplier_id,
        quantity=order_data.quantity,
        status=order_data.status,
        expected_delivery=order_data.expected_delivery
    )

    db.add(restock_order)
    db.commit()
    db.refresh(restock_order)

    return restock_order


# -----------------------------
# Get All Restock Orders
# -----------------------------

@router.get("/", response_model=list[RestockOrderResponse])
def get_restock_orders(
    db: Session = Depends(get_db)
):

    orders = db.query(RestockOrder).all()

    return orders


# -----------------------------
# Get Restock Order By ID
# -----------------------------

@router.get("/{order_id}", response_model=RestockOrderResponse)
def get_restock_order(
    order_id: int,
    db: Session = Depends(get_db)
):

    order = db.query(RestockOrder).filter(
        RestockOrder.id == order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Restock order not found"
        )

    return order


# -----------------------------
# Update Restock Order Status
# -----------------------------

@router.put("/{order_id}/status")
def update_restock_order_status(
    order_id: int,
    status: str,
    db: Session = Depends(get_db)
):

    order = db.query(RestockOrder).filter(
        RestockOrder.id == order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Restock order not found"
        )

    order.status = status

    db.commit()
    db.refresh(order)

    return {
        "message": "Restock order status updated successfully",
        "order_id": order.id,
        "status": order.status
    }


# -----------------------------
# Delete Restock Order
# -----------------------------

@router.delete("/{order_id}")
def delete_restock_order(
    order_id: int,
    db: Session = Depends(get_db)
):

    order = db.query(RestockOrder).filter(
        RestockOrder.id == order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Restock order not found"
        )

    db.delete(order)
    db.commit()

    return {
        "message": "Restock order deleted successfully"
    }