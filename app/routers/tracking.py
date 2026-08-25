from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Delivery, TrackingEvent
from app.schemas import (
    TrackingEventCreate,
    TrackingEventResponse,
    DeliveryResponse
)


router = APIRouter(
    prefix="/tracking",
    tags=["Shipment Tracking"]
)


# ============================================================
# GET SHIPMENT BY TRACKING NUMBER
# ============================================================

@router.get(
    "/shipment/{tracking_number}",
    response_model=DeliveryResponse
)
def get_shipment_by_tracking_number(
    tracking_number: str,
    db: Session = Depends(get_db)
):
    shipment = db.query(Delivery).filter(
        Delivery.tracking_number == tracking_number
    ).first()

    if not shipment:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found"
        )

    return shipment


# ============================================================
# GET SHIPMENT BY DELIVERY ID
# ============================================================

@router.get(
    "/shipment/id/{delivery_id}",
    response_model=DeliveryResponse
)
def get_shipment_by_id(
    delivery_id: int,
    db: Session = Depends(get_db)
):
    shipment = db.query(Delivery).filter(
        Delivery.id == delivery_id
    ).first()

    if not shipment:
        raise HTTPException(
            status_code=404,
            detail="Shipment not found"
        )

    return shipment


# ============================================================
# GET SHIPMENT BY TRAILER ID
# ============================================================

@router.get(
    "/trailer/{trailer_id}",
    response_model=DeliveryResponse
)
def get_shipment_by_trailer_id(
    trailer_id: str,
    db: Session = Depends(get_db)
):
    shipment = db.query(Delivery).filter(
        Delivery.trailer_id == trailer_id
    ).first()

    if not shipment:
        raise HTTPException(
            status_code=404,
            detail="Shipment with this trailer ID was not found"
        )

    return shipment


# ============================================================
# GET SHIPMENT BY SHIPMENT REFERENCE
# ============================================================

@router.get(
    "/reference/{shipment_reference}",
    response_model=DeliveryResponse
)
def get_shipment_by_reference(
    shipment_reference: str,
    db: Session = Depends(get_db)
):
    shipment = db.query(Delivery).filter(
        Delivery.shipment_reference == shipment_reference
    ).first()

    if not shipment:
        raise HTTPException(
            status_code=404,
            detail="Shipment with this reference was not found"
        )

    return shipment


# ============================================================
# ADD TRACKING EVENT
# ============================================================

@router.post(
    "/{delivery_id}/events",
    response_model=TrackingEventResponse,
    status_code=201
)
def add_tracking_event(
    delivery_id: int,
    event_data: TrackingEventCreate,
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

    event = TrackingEvent(
        delivery_id=delivery_id,
        status=event_data.status,
        location=event_data.location,
        latitude=event_data.latitude,
        longitude=event_data.longitude,
        event_time=event_data.event_time or datetime.utcnow(),
        description=event_data.description
    )

    db.add(event)

    # Update current shipment state
    delivery.status = event_data.status

    if event_data.latitude is not None:
        delivery.current_latitude = event_data.latitude

    if event_data.longitude is not None:
        delivery.current_longitude = event_data.longitude

    if event_data.location:
        delivery.current_location = event_data.location

    delivery.last_gps_update = datetime.utcnow()

    db.commit()
    db.refresh(event)

    return event


# ============================================================
# GET TRACKING HISTORY
# ============================================================

@router.get(
    "/{delivery_id}/events",
    response_model=list[TrackingEventResponse]
)
def get_tracking_history(
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

    return db.query(TrackingEvent).filter(
        TrackingEvent.delivery_id == delivery_id
    ).order_by(
        TrackingEvent.event_time.asc()
    ).all()


# ============================================================
# GET ACTIVE SHIPMENTS
# ============================================================

@router.get(
    "/active",
    response_model=list[DeliveryResponse]
)
def get_active_shipments(
    db: Session = Depends(get_db)
):
    active_statuses = [
        "scheduled",
        "in_transit",
        "delayed",
        "arrived",
        "unloading"
    ]

    return db.query(Delivery).filter(
        Delivery.status.in_(active_statuses)
    ).all()