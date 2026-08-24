from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Delivery, Alert


router = APIRouter(
    prefix="/operations",
    tags=["Operations"]
)


# ============================================================
# RESPONSE SCHEMA
# ============================================================

class AlertResponse(BaseModel):
    id: int
    delivery_id: int
    alert_type: str
    severity: str
    title: str
    message: str
    created_at: datetime
    resolved: bool

    class Config:
        from_attributes = True


# ============================================================
# DELAY DETECTION
# ============================================================

@router.post("/detect-delays")
def detect_delays(
    db: Session = Depends(get_db)
):

    deliveries = db.query(Delivery).all()

    detected = []

    now = datetime.utcnow()

    for delivery in deliveries:

        delay = False

        if (
            delivery.scheduled_arrival
            and delivery.estimated_arrival
        ):

            if delivery.estimated_arrival > delivery.scheduled_arrival:
                delay = True

        elif (
            delivery.scheduled_arrival
            and delivery.status
            not in {"delivered", "arrived"}
        ):

            if now > delivery.scheduled_arrival:
                delay = True

        if delay:

            delivery.delay_detected = True
            delivery.status = "delayed"

            existing = db.query(Alert).filter(
                Alert.delivery_id == delivery.id,
                Alert.alert_type == "delay",
                Alert.resolved == False
            ).first()

            if not existing:

                alert = Alert(
                    delivery_id=delivery.id,
                    alert_type="delay",
                    severity="high",
                    title="Shipment Delay Detected",
                    message=(
                        f"Delivery {delivery.id} is "
                        "expected to arrive late."
                    )
                )

                db.add(alert)

            detected.append(delivery.id)

    db.commit()

    return {
        "delayed_shipments": detected,
        "count": len(detected)
    }


# ============================================================
# EXCEPTION DETECTION
# ============================================================

@router.post("/detect-exceptions")
def detect_exceptions(
    db: Session = Depends(get_db)
):

    deliveries = db.query(Delivery).all()

    exceptions = []

    for delivery in deliveries:

        exception = False
        reason = None

        # Missing GPS
        if (
            delivery.status == "in_transit"
            and delivery.last_gps_update is None
        ):
            exception = True
            reason = "GPS location has not been received"

        # Simulation with missing coordinates
        elif (
            delivery.simulation_active
            and (
                delivery.current_latitude is None
                or delivery.current_longitude is None
            )
        ):
            exception = True
            reason = "Shipment has invalid GPS coordinates"

        # Delivery without dock after arrival
        elif (
            delivery.status in {
                "arrived",
                "unloading"
            }
            and delivery.dock_id is None
        ):
            exception = True
            reason = "Arrived shipment has no assigned dock"

        if exception:

            delivery.exception_detected = True

            existing = db.query(Alert).filter(
                Alert.delivery_id == delivery.id,
                Alert.alert_type == "exception",
                Alert.resolved == False
            ).first()

            if not existing:

                alert = Alert(
                    delivery_id=delivery.id,
                    alert_type="exception",
                    severity="critical",
                    title="Shipment Exception",
                    message=reason
                )

                db.add(alert)

            exceptions.append({
                "delivery_id": delivery.id,
                "reason": reason
            })

    db.commit()

    return {
        "exceptions": exceptions,
        "count": len(exceptions)
    }


# ============================================================
# GET ALERTS
# ============================================================

@router.get(
    "/alerts",
    response_model=List[AlertResponse]
)
def get_alerts(
    db: Session = Depends(get_db)
):

    return db.query(Alert).filter(
        Alert.resolved == False
    ).order_by(
        Alert.created_at.desc()
    ).all()


# ============================================================
# RESOLVE ALERT
# ============================================================

@router.put("/alerts/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):

    alert = db.query(Alert).filter(
        Alert.id == alert_id
    ).first()

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found"
        )

    alert.resolved = True

    db.commit()

    return {
        "message": "Alert resolved successfully",
        "alert_id": alert.id
    }