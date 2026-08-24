from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Delivery, RestockOrder, YardDock
from app.schemas import DeliveryCreate, DeliveryResponse


router = APIRouter(
    prefix="/deliveries",
    tags=["Deliveries"]
)


# ============================================================
# CREATE DELIVERY / SHIPMENT
# ============================================================

@router.post(
    "/",
    response_model=DeliveryResponse,
    status_code=201
)
def create_delivery(
    delivery_data: DeliveryCreate,
    db: Session = Depends(get_db)
):

    order = db.query(RestockOrder).filter(
        RestockOrder.id == delivery_data.restock_order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Restock order not found"
        )

    if delivery_data.dock_id is not None:

        dock = db.query(YardDock).filter(
            YardDock.id == delivery_data.dock_id
        ).first()

        if not dock:
            raise HTTPException(
                status_code=404,
                detail="Yard dock not found"
            )

    if delivery_data.tracking_number:

        existing = db.query(Delivery).filter(
            Delivery.tracking_number ==
            delivery_data.tracking_number
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Tracking number already exists"
            )

    delivery = Delivery(
        restock_order_id=delivery_data.restock_order_id,
        dock_id=delivery_data.dock_id,
        tracking_number=delivery_data.tracking_number,
        trailer_id=delivery_data.trailer_id,
        shipment_reference=delivery_data.shipment_reference,
        carrier=delivery_data.carrier,
        status=delivery_data.status,
        scheduled_arrival=delivery_data.scheduled_arrival,
        actual_arrival=delivery_data.actual_arrival,
        current_latitude=delivery_data.current_latitude,
        current_longitude=delivery_data.current_longitude,
        current_location=delivery_data.current_location,
        destination_latitude=delivery_data.destination_latitude,
        destination_longitude=delivery_data.destination_longitude,
        estimated_arrival=delivery_data.estimated_arrival,
        eta_minutes=delivery_data.eta_minutes,
        average_speed_kmph=delivery_data.average_speed_kmph,
        distance_remaining_km=delivery_data.distance_remaining_km,
        simulation_active=delivery_data.simulation_active
    )

    db.add(delivery)
    db.commit()
    db.refresh(delivery)

    return delivery


# ============================================================
# GET ALL DELIVERIES
# ============================================================

@router.get(
    "/",
    response_model=list[DeliveryResponse]
)
def get_deliveries(
    db: Session = Depends(get_db)
):
    return db.query(Delivery).all()


# ============================================================
# GET DELIVERY BY ID
# ============================================================

@router.get(
    "/{delivery_id}",
    response_model=DeliveryResponse
)
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


# ============================================================
# GET BY TRACKING NUMBER
# ============================================================

@router.get(
    "/tracking/{tracking_number}",
    response_model=DeliveryResponse
)
def get_delivery_by_tracking_number(
    tracking_number: str,
    db: Session = Depends(get_db)
):

    delivery = db.query(Delivery).filter(
        Delivery.tracking_number == tracking_number
    ).first()

    if not delivery:
        raise HTTPException(
            status_code=404,
            detail="Shipment with this tracking number was not found"
        )

    return delivery


# ============================================================
# UPDATE STATUS
# ============================================================

@router.put(
    "/{delivery_id}/status",
    response_model=DeliveryResponse
)
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

    allowed_statuses = {
        "scheduled",
        "in_transit",
        "delayed",
        "arrived",
        "unloading",
        "delivered",
        "cancelled"
    }

    normalized_status = status.lower().strip()

    if normalized_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid delivery status",
                "allowed_statuses": sorted(allowed_statuses)
            }
        )

    delivery.status = normalized_status

    if normalized_status in {"arrived", "delivered"}:

        if delivery.actual_arrival is None:
            delivery.actual_arrival = datetime.utcnow()

    db.commit()
    db.refresh(delivery)

    return delivery