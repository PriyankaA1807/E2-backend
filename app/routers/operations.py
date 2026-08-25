from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Delivery, Alert, YardDock
from app.schemas import (
    AlertResponse,
    DockUnavailableDetectionResponse,
    DockReassignmentRequiredResponse
)


router = APIRouter(
    prefix="/operations",
    tags=["Operations"]
)


# ============================================================
# DELAY DETECTION
# ============================================================

@router.post("/detect-delays")
def detect_delays(
    db: Session = Depends(get_db)
):
    deliveries = db.query(
        Delivery
    ).all()

    detected = []

    now = datetime.utcnow()

    for delivery in deliveries:

        delay = False

        # ----------------------------------------------------
        # Predicted arrival later than scheduled arrival
        # ----------------------------------------------------

        if (
            delivery.scheduled_arrival
            and delivery.estimated_arrival
        ):

            if (
                delivery.estimated_arrival
                > delivery.scheduled_arrival
            ):
                delay = True

        # ----------------------------------------------------
        # Scheduled arrival already passed
        # ----------------------------------------------------

        elif (
            delivery.scheduled_arrival
            and delivery.status
            not in {
                "completed",
                "departed",
                "cancelled",
                "arrived_at_gate",
                "in_yard",
                "waiting_for_dock",
                "dock_assigned",
                "docked",
                "unloading",
                "arrived"
            }
        ):

            if (
                now
                > delivery.scheduled_arrival
            ):
                delay = True

        # ----------------------------------------------------
        # Process delay
        # ----------------------------------------------------

        if delay:

            delivery.delay_detected = True

            if delivery.status in {
                "scheduled",
                "in_transit"
            }:

                delivery.status = "delayed"

            existing = db.query(
                Alert
            ).filter(
                Alert.delivery_id
                == delivery.id,

                Alert.alert_type
                == "delay",

                Alert.resolved
                == False
            ).first()

            if not existing:

                alert = Alert(
                    delivery_id=delivery.id,

                    alert_type="delay",

                    severity="high",

                    title=(
                        "Shipment Delay Detected"
                    ),

                    message=(
                        f"Delivery {delivery.id} "
                        "is expected to arrive late."
                    )
                )

                db.add(alert)

            detected.append(
                delivery.id
            )

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
    deliveries = db.query(
        Delivery
    ).all()

    exceptions = []

    for delivery in deliveries:

        exception = False
        reason = None

        # ----------------------------------------------------
        # Missing GPS
        # ----------------------------------------------------

        if (
            delivery.status == "in_transit"
            and delivery.last_gps_update is None
        ):

            exception = True

            reason = (
                "GPS location has not been received"
            )

        # ----------------------------------------------------
        # Invalid/missing GPS while simulating
        # ----------------------------------------------------

        elif (
            delivery.simulation_active
            and (
                delivery.current_latitude is None
                or delivery.current_longitude is None
            )
        ):

            exception = True

            reason = (
                "Shipment has invalid GPS coordinates"
            )

        # ----------------------------------------------------
        # Arrived trailer without dock
        # ----------------------------------------------------

        elif (
            delivery.status in {
                "arrived_at_gate",
                "in_yard",
                "waiting_for_dock",
                "dock_assigned",
                "docked",
                "unloading",
                "arrived"
            }
            and delivery.dock_id is None
        ):

            exception = True

            reason = (
                "Arrived shipment has no assigned dock"
            )

        if exception:

            delivery.exception_detected = True

            existing = db.query(
                Alert
            ).filter(
                Alert.delivery_id
                == delivery.id,

                Alert.alert_type
                == "exception",

                Alert.resolved
                == False
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

            exceptions.append(
                {
                    "delivery_id": (
                        delivery.id
                    ),
                    "reason": reason
                }
            )

    db.commit()

    return {
        "exceptions": exceptions,
        "count": len(exceptions)
    }


# ============================================================
# DOCK UNAVAILABLE DETECTION
# ============================================================

@router.post(
    "/detect-dock-unavailable",
    response_model=DockUnavailableDetectionResponse
)
def detect_dock_unavailable(
    db: Session = Depends(get_db)
):
    unavailable_statuses = {
        "blocked",
        "maintenance",
        "occupied"
    }

    deliveries = db.query(
        Delivery
    ).filter(
        Delivery.dock_id.isnot(None)
    ).all()

    detected = []

    for delivery in deliveries:

        dock = db.query(
            YardDock
        ).filter(
            YardDock.id
            == delivery.dock_id
        ).first()

        if not dock:
            continue

        dock_status = (
            dock.status.lower().strip()
            if dock.status
            else ""
        )

        if (
            dock_status
            not in unavailable_statuses
        ):
            continue

        existing = db.query(
            Alert
        ).filter(
            Alert.delivery_id
            == delivery.id,

            Alert.alert_type
            == "dock_unavailable",

            Alert.resolved
            == False
        ).first()

        if not existing:

            trailer_label = (
                delivery.trailer_id
                or delivery.tracking_number
                or f"delivery {delivery.id}"
            )

            alert = Alert(
                delivery_id=delivery.id,

                alert_type="dock_unavailable",

                severity="high",

                title=(
                    "Assigned Dock Unavailable"
                ),

                message=(
                    f"Dock {dock.dock_number} "
                    f"at {dock.yard_name} is "
                    f"{dock_status} for trailer "
                    f"{trailer_label}."
                )
            )

            db.add(alert)

        delivery.exception_detected = True

        detected.append(
            {
                "delivery_id": (
                    delivery.id
                ),

                "tracking_number": (
                    delivery.tracking_number
                ),

                "trailer_id": (
                    delivery.trailer_id
                ),

                "dock_id": (
                    dock.id
                ),

                "dock_number": (
                    dock.dock_number
                ),

                "dock_status": (
                    dock_status
                )
            }
        )

    db.commit()

    return {
        "dock_unavailable": detected,
        "count": len(detected)
    }


# ============================================================
# DOCK REASSIGNMENT REQUIRED
# ============================================================

@router.post(
    "/detect-reassignment-required",
    response_model=DockReassignmentRequiredResponse
)
def detect_reassignment_required(
    db: Session = Depends(get_db)
):
    unavailable_statuses = {
        "blocked",
        "maintenance",
        "occupied"
    }

    deliveries = db.query(
        Delivery
    ).filter(
        Delivery.dock_id.isnot(None)
    ).all()

    detected = []

    for delivery in deliveries:

        dock = db.query(
            YardDock
        ).filter(
            YardDock.id
            == delivery.dock_id
        ).first()

        if not dock:
            continue

        dock_status = (
            dock.status.lower().strip()
            if dock.status
            else ""
        )

        if (
            dock_status
            not in unavailable_statuses
        ):
            continue

        # ----------------------------------------------------
        # Avoid duplicate unresolved alerts
        # ----------------------------------------------------

        existing = db.query(
            Alert
        ).filter(
            Alert.delivery_id
            == delivery.id,

            Alert.alert_type
            == "dock_reassignment_required",

            Alert.resolved
            == False
        ).first()

        if not existing:

            trailer_label = (
                delivery.trailer_id
                or delivery.tracking_number
                or f"delivery {delivery.id}"
            )

            alert = Alert(
                delivery_id=delivery.id,

                alert_type=(
                    "dock_reassignment_required"
                ),

                severity="high",

                title=(
                    "Dock Reassignment Required"
                ),

                message=(
                    f"Trailer {trailer_label} "
                    "requires dock reassignment "
                    f"because dock {dock.dock_number} "
                    f"at {dock.yard_name} is "
                    f"{dock_status}."
                )
            )

            db.add(alert)

        delivery.exception_detected = True

        detected.append(
            {
                "delivery_id": (
                    delivery.id
                ),

                "tracking_number": (
                    delivery.tracking_number
                ),

                "trailer_id": (
                    delivery.trailer_id
                ),

                "current_dock_id": (
                    dock.id
                ),

                "current_dock_number": (
                    dock.dock_number
                ),

                "dock_status": (
                    dock_status
                ),

                "reassignment_required": True
            }
        )

    db.commit()

    return {
        "reassignment_required": detected,
        "count": len(detected)
    }


# ============================================================
# GET ACTIVE ALERTS
# ============================================================

@router.get(
    "/alerts",
    response_model=list[AlertResponse]
)
def get_alerts(
    db: Session = Depends(get_db)
):
    return db.query(
        Alert
    ).filter(
        Alert.resolved
        == False
    ).order_by(
        Alert.created_at.desc()
    ).all()


# ============================================================
# RESOLVE ALERT
# ============================================================

@router.put(
    "/alerts/{alert_id}/resolve"
)
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    alert = db.query(
        Alert
    ).filter(
        Alert.id
        == alert_id
    ).first()

    if not alert:

        raise HTTPException(
            status_code=404,
            detail="Alert not found"
        )

    alert.resolved = True

    db.commit()

    return {
        "message": (
            "Alert resolved successfully"
        ),
        "alert_id": alert.id
    }