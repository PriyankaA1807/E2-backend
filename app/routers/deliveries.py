from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Delivery, RestockOrder, YardDock

from datetime import datetime

router = APIRouter(
    prefix="/deliveries",
    tags=["Deliveries"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
def create_delivery(
    restock_order_id: int,
    tracking_number: str,
    carrier: str,
    dock_id: int,
    status: str = "in_transit",
    scheduled_arrival: datetime | None = None,
    db: Session = Depends(get_db)
):
    # Check restock order
    order = db.query(RestockOrder).filter(
        RestockOrder.id == restock_order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Restock order not found"
        )

    # Check dock
    dock = db.query(YardDock).filter(
        YardDock.id == dock_id
    ).first()

    if not dock:
        raise HTTPException(
            status_code=404,
            detail="Yard dock not found"
        )

    # Create delivery
    delivery = Delivery(
        restock_order_id=restock_order_id,
        dock_id=dock_id,
        tracking_number=tracking_number,
        carrier=carrier,
        status=status,
        scheduled_arrival=scheduled_arrival
    )

    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    return delivery


@router.get("/")
def get_deliveries(
    db: Session = Depends(get_db)
):
    return db.query(Delivery).all()


@router.get("/{delivery_id}")
def get_delivery(
    delivery_id: int,
    db: Session = Depends(get_db)
):
    delivery = db.query(Delivery).filter(
        Delivery.id == delivery_id
    ).first()

    if not delivery:
        raise HTTPException(
            status_code=404,
            detail="Delivery not found"
        )

    return delivery


@router.put("/{delivery_id}/status")
def update_delivery_status(
    delivery_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    delivery = db.query(Delivery).filter(
        Delivery.id == delivery_id
    ).first()

    if not delivery:
        raise HTTPException(
            status_code=404,
            detail="Delivery not found"
        )

    delivery.status = status

    # If delivery arrives, record actual arrival
    if status.lower() == "delivered":
        delivery.actual_arrival = datetime.utcnow()

    db.commit()
    db.refresh(delivery)

    return delivery