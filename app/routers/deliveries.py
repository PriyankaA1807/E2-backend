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
# DELIVERY / TRAILER STATUS FLOW
# ============================================================

ALLOWED_TRANSITIONS = {
    "scheduled": {
        "in_transit",
        "cancelled"
    },

    "in_transit": {
        "delayed",
        "arrived_at_gate",
        "cancelled"
    },

    # A delayed truck can recover and continue travelling,
    # or it may eventually reach the yard.
    "delayed": {
        "in_transit",
        "arrived_at_gate",
        "cancelled"
    },

    "arrived_at_gate": {
        "in_yard"
    },

    "in_yard": {
        "waiting_for_dock"
    },

    "waiting_for_dock": {
        "dock_assigned"
    },

    "dock_assigned": {
        "docked",
        "waiting_for_dock"
    },

    "docked": {
        "unloading"
    },

    "unloading": {
        "completed"
    },

    "completed": {
        "departed"
    },

    "departed": set(),

    "cancelled": set()
}


VALID_STATUSES = set(ALLOWED_TRANSITIONS.keys())


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

    # --------------------------------------------------------
    # Check Restock Order
    # --------------------------------------------------------

    order = db.query(RestockOrder).filter(
        RestockOrder.id == delivery_data.restock_order_id
    ).first()

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Restock order not found"
        )

    # --------------------------------------------------------
    # Check Dock
    # --------------------------------------------------------

    if delivery_data.dock_id is not None:

        dock = db.query(YardDock).filter(
            YardDock.id == delivery_data.dock_id
        ).first()

        if not dock:
            raise HTTPException(
                status_code=404,
                detail="Yard dock not found"
            )

    # --------------------------------------------------------
    # Check Tracking Number Uniqueness
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Check Trailer ID Uniqueness
    # --------------------------------------------------------

    if delivery_data.trailer_id:

        existing_trailer = db.query(Delivery).filter(
            Delivery.trailer_id == delivery_data.trailer_id
        ).first()

        if existing_trailer:
            raise HTTPException(
                status_code=400,
                detail="Trailer ID already exists"
            )

    # --------------------------------------------------------
    # Check Shipment Reference Uniqueness
    # --------------------------------------------------------

    if delivery_data.shipment_reference:

        existing_reference = db.query(Delivery).filter(
            Delivery.shipment_reference ==
            delivery_data.shipment_reference
        ).first()

        if existing_reference:
            raise HTTPException(
                status_code=400,
                detail="Shipment reference already exists"
            )

    # --------------------------------------------------------
    # Validate Initial Status
    # --------------------------------------------------------

    normalized_status = (
        delivery_data.status.lower().strip()
        if delivery_data.status
        else "scheduled"
    )

    if normalized_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid initial delivery status",
                "allowed_statuses": sorted(VALID_STATUSES)
            }
        )

    # New deliveries should normally start as scheduled.
    if normalized_status != "scheduled":
        raise HTTPException(
            status_code=400,
            detail={
                "message": (
                    "A new delivery must start with status 'scheduled'"
                )
            }
        )

    # --------------------------------------------------------
    # Create Delivery
    # --------------------------------------------------------

    delivery = Delivery(
        restock_order_id=delivery_data.restock_order_id,
        dock_id=delivery_data.dock_id,
        tracking_number=delivery_data.tracking_number,
        trailer_id=delivery_data.trailer_id,
        shipment_reference=delivery_data.shipment_reference,
        carrier=delivery_data.carrier,

        status=normalized_status,

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
# GET DELIVERY BY TRACKING NUMBER
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
# UPDATE DELIVERY / TRAILER STATUS
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

    new_status = status.lower().strip()

    # --------------------------------------------------------
    # Validate requested status
    # --------------------------------------------------------

    if new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid delivery status",
                "allowed_statuses": sorted(VALID_STATUSES)
            }
        )

    current_status = (
        delivery.status.lower().strip()
        if delivery.status
        else "scheduled"
    )

    # --------------------------------------------------------
    # Same status — no change required
    # --------------------------------------------------------

    if current_status == new_status:
        return delivery

    # --------------------------------------------------------
    # Handle old status values
    # --------------------------------------------------------

    legacy_status_map = {
        "arrived": "arrived_at_gate",
        "delivered": "completed"
    }

    current_status = legacy_status_map.get(
        current_status,
        current_status
    )

    # --------------------------------------------------------
    # Make sure current status is recognized
    # --------------------------------------------------------

    if current_status not in ALLOWED_TRANSITIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "message": (
                    f"Current delivery status '{delivery.status}' "
                    "is not part of the supported lifecycle"
                )
            }
        )

    # --------------------------------------------------------
    # Validate lifecycle transition
    # --------------------------------------------------------

    allowed_next_statuses = ALLOWED_TRANSITIONS[current_status]

    if new_status not in allowed_next_statuses:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid delivery status transition",
                "current_status": current_status,
                "requested_status": new_status,
                "allowed_next_statuses": sorted(
                    allowed_next_statuses
                )
            }
        )

    # --------------------------------------------------------
    # Update status
    # --------------------------------------------------------

    delivery.status = new_status

    # Truck has reached the facility.
    if new_status == "arrived_at_gate":

        if delivery.actual_arrival is None:
            delivery.actual_arrival = datetime.utcnow()

    # Once completed/departed, simulation should stop.
    if new_status in {
        "completed",
        "departed",
        "cancelled"
    }:
        delivery.simulation_active = False

    db.commit()
    db.refresh(delivery)

    return delivery