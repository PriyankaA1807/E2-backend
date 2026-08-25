from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Delivery, YardDock
from app.schemas import (
    DockAssignmentRequest,
    DockRecommendationResponse,
    DeliveryResponse,
    DockScheduleResponse
)


router = APIRouter(
    prefix="/dock-operations",
    tags=["Dock Operations"]
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_DOCK_SLOT_MINUTES = 30


# ============================================================
# DOCK COMPATIBILITY
# ============================================================

def calculate_dock_score(
    delivery: Delivery,
    dock: YardDock
):
    score = 0
    reasons = []

    if dock.status != "available":
        return 0, False, ["Dock is not available"]

    score += 50
    reasons.append("Dock is available")

    if getattr(
        dock,
        "supported_vehicle_type",
        None
    ) == "truck":
        score += 20
        reasons.append(
            "Vehicle type compatible"
        )

    if getattr(
        dock,
        "refrigerated",
        False
    ):
        score += 10
        reasons.append(
            "Refrigerated capability available"
        )

    if dock.dock_type == "standard":
        score += 10
        reasons.append(
            "Standard dock suitable for shipment"
        )

    if delivery.delay_detected:
        score += 10
        reasons.append(
            "Delayed shipment receives priority"
        )

    return score, True, reasons


# ============================================================
# HELPER: EFFECTIVE ARRIVAL
# ============================================================

def get_effective_arrival(
    delivery: Delivery
):
    if delivery.actual_arrival is not None:
        return delivery.actual_arrival

    if delivery.estimated_arrival is not None:
        return delivery.estimated_arrival

    if delivery.scheduled_arrival is not None:
        return delivery.scheduled_arrival

    return None


# ============================================================
# HELPER: DELIVERY PRIORITY
# ============================================================

def get_delivery_priority(
    delivery: Delivery
):
    priority_value = getattr(
        delivery,
        "priority",
        None
    )

    if isinstance(
        priority_value,
        str
    ):
        priority_map = {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "normal": 1,
            "low": 0
        }

        return priority_map.get(
            priority_value.lower(),
            1
        )

    if delivery.delay_detected:
        return 3

    if delivery.status in {
        "arrived_at_gate",
        "in_yard",
        "waiting_for_dock"
    }:
        return 2

    return 1


# ============================================================
# HELPER: LOAD TYPE
# ============================================================

def get_load_type(
    delivery: Delivery
):
    load_type = getattr(
        delivery,
        "load_type",
        None
    )

    if load_type:
        return load_type

    return "standard"


# ============================================================
# RECOMMEND DOCKS
# ============================================================

@router.get(
    "/recommend/{delivery_id}",
    response_model=list[DockRecommendationResponse]
)
def recommend_docks(
    delivery_id: int,
    db: Session = Depends(get_db)
):
    delivery = db.query(
        Delivery
    ).filter(
        Delivery.id == delivery_id
    ).first()

    if not delivery:
        raise HTTPException(
            status_code=404,
            detail="Delivery not found"
        )

    docks = db.query(
        YardDock
    ).all()

    recommendations = []

    for dock in docks:

        score, compatible, reasons = (
            calculate_dock_score(
                delivery,
                dock
            )
        )

        recommendations.append(
            DockRecommendationResponse(
                dock_id=dock.id,
                yard_name=dock.yard_name,
                dock_number=dock.dock_number,
                score=score,
                compatible=compatible,
                reasons=reasons
            )
        )

    recommendations.sort(
        key=lambda item: item.score,
        reverse=True
    )

    return recommendations


# ============================================================
# ARRIVAL-WINDOW DOCK SCHEDULE
# ============================================================

@router.get(
    "/schedule",
    response_model=DockScheduleResponse
)
def get_dock_schedule(
    db: Session = Depends(get_db)
):
    inactive_statuses = {
        "completed",
        "departed",
        "cancelled"
    }

    deliveries = db.query(
        Delivery
    ).filter(
        ~Delivery.status.in_(
            inactive_statuses
        )
    ).all()

    docks = db.query(
        YardDock
    ).all()

    # ========================================================
    # NO DOCKS CONFIGURED
    # ========================================================

    if not docks:

        unscheduled = [
            {
                "delivery_id": delivery.id,

                "tracking_number": (
                    delivery.tracking_number
                ),

                "trailer_id": (
                    delivery.trailer_id
                ),

                "shipment_reference": (
                    delivery.shipment_reference
                ),

                "status": (
                    delivery.status
                ),

                "reason": (
                    "No docks configured"
                )
            }

            for delivery in deliveries
        ]

        return {
            "generated_at": (
                datetime.utcnow()
            ),

            "slot_duration_minutes": (
                DEFAULT_DOCK_SLOT_MINUTES
            ),

            "total_incoming_trailers": (
                len(deliveries)
            ),

            "total_docks": 0,

            "scheduled_count": 0,

            "unscheduled_count": (
                len(unscheduled)
            ),

            "schedule": [],

            "unscheduled": (
                unscheduled
            )
        }

    # ========================================================
    # BUILD SCHEDULING CANDIDATES
    # ========================================================

    scheduling_candidates = []

    for delivery in deliveries:

        arrival_time = (
            get_effective_arrival(
                delivery
            )
        )

        if arrival_time is None:
            continue

        scheduling_candidates.append(
            {
                "delivery": (
                    delivery
                ),

                "arrival_time": (
                    arrival_time
                ),

                "priority": (
                    get_delivery_priority(
                        delivery
                    )
                )
            }
        )

    # ========================================================
    # SORT BY ARRIVAL + PRIORITY
    # ========================================================

    scheduling_candidates.sort(
        key=lambda item: (
            item["arrival_time"],
            -item["priority"]
        )
    )

    now = datetime.utcnow()

    # ========================================================
    # NEXT AVAILABLE TIME FOR EACH DOCK
    # ========================================================

    dock_next_available = {}

    for dock in docks:

        if dock.status == "available":

            dock_next_available[
                dock.id
            ] = now

        elif dock.status == "reserved":

            dock_next_available[
                dock.id
            ] = (
                now
                + timedelta(
                    minutes=(
                        DEFAULT_DOCK_SLOT_MINUTES
                    )
                )
            )

        else:

            # blocked / maintenance / occupied
            # are treated as unusable for scheduling.
            dock_next_available[
                dock.id
            ] = None

    schedule = []

    scheduled_delivery_ids = set()

    # ========================================================
    # SCHEDULE EACH TRAILER
    # ========================================================

    for item in scheduling_candidates:

        delivery = (
            item["delivery"]
        )

        arrival_time = (
            item["arrival_time"]
        )

        priority = (
            item["priority"]
        )

        best_dock = None
        best_start_time = None
        best_score = -1
        best_reasons = []

        # ====================================================
        # PRESERVE EXISTING ASSIGNMENT ONLY IF USABLE
        # ====================================================

        if (
            delivery.dock_id
            is not None
        ):

            existing_dock = db.query(
                YardDock
            ).filter(
                YardDock.id
                == delivery.dock_id
            ).first()

            if (
                existing_dock
                and existing_dock.status
                not in {
                    "blocked",
                    "maintenance",
                    "occupied"
                }
                and dock_next_available.get(
                    existing_dock.id
                ) is not None
            ):

                start_time = max(
                    arrival_time,

                    dock_next_available.get(
                        existing_dock.id,
                        now
                    )
                )

                best_dock = (
                    existing_dock
                )

                best_start_time = (
                    start_time
                )

                best_score = 100

                best_reasons = [
                    (
                        "Existing dock assignment "
                        "preserved"
                    )
                ]

        # ====================================================
        # FIND BEST REPLACEMENT / NEW DOCK
        # ====================================================

        if best_dock is None:

            for dock in docks:

                # --------------------------------------------
                # Skip unusable docks completely
                # --------------------------------------------

                if dock.status in {
                    "blocked",
                    "maintenance",
                    "occupied"
                }:
                    continue

                available_at = (
                    dock_next_available.get(
                        dock.id
                    )
                )

                if available_at is None:
                    continue

                score = 0
                reasons = []

                # --------------------------------------------
                # VEHICLE TYPE
                # --------------------------------------------

                supported_vehicle = getattr(
                    dock,
                    "supported_vehicle_type",
                    None
                )

                if supported_vehicle in {
                    None,
                    "truck"
                }:

                    score += 20

                    reasons.append(
                        "Vehicle type compatible"
                    )

                else:
                    continue

                # --------------------------------------------
                # LOAD TYPE
                # --------------------------------------------

                load_type = (
                    get_load_type(
                        delivery
                    )
                )

                if (
                    load_type == "standard"
                    and dock.dock_type
                    == "standard"
                ):

                    score += 20

                    reasons.append(
                        "Load type compatible"
                    )

                # --------------------------------------------
                # CURRENT AVAILABILITY
                # --------------------------------------------

                if dock.status == "available":

                    score += 30

                    reasons.append(
                        "Dock currently available"
                    )

                elif dock.status == "reserved":

                    reasons.append(
                        "Dock available after existing slot"
                    )

                # --------------------------------------------
                # CALCULATE SLOT
                # --------------------------------------------

                proposed_start = max(
                    arrival_time,
                    available_at
                )

                waiting_minutes = max(
                    0,

                    (
                        proposed_start
                        - arrival_time
                    ).total_seconds()
                    / 60
                )

                # --------------------------------------------
                # WAITING TIME SCORE
                # --------------------------------------------

                if waiting_minutes <= 5:

                    score += 30

                    reasons.append(
                        "Minimal waiting time"
                    )

                elif waiting_minutes <= 30:

                    score += 20

                    reasons.append(
                        "Acceptable waiting time"
                    )

                elif waiting_minutes <= 60:

                    score += 10

                    reasons.append(
                        "Moderate waiting time"
                    )

                # --------------------------------------------
                # PRIORITY
                # --------------------------------------------

                score += (
                    priority * 5
                )

                if priority >= 3:

                    reasons.append(
                        "High operational priority"
                    )

                # --------------------------------------------
                # SELECT BEST DOCK
                # --------------------------------------------

                if score > best_score:

                    best_score = (
                        score
                    )

                    best_dock = (
                        dock
                    )

                    best_start_time = (
                        proposed_start
                    )

                    best_reasons = (
                        reasons
                    )

        # ====================================================
        # NOTHING AVAILABLE
        # ====================================================

        if best_dock is None:
            continue

        # ====================================================
        # CREATE TIME WINDOW
        # ====================================================

        end_time = (
            best_start_time
            + timedelta(
                minutes=(
                    DEFAULT_DOCK_SLOT_MINUTES
                )
            )
        )

        dock_next_available[
            best_dock.id
        ] = end_time

        scheduled_delivery_ids.add(
            delivery.id
        )

        schedule.append(
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

                "shipment_reference": (
                    delivery.shipment_reference
                ),

                "delivery_status": (
                    delivery.status
                ),

                "load_type": (
                    get_load_type(
                        delivery
                    )
                ),

                "priority_score": (
                    priority
                ),

                "scheduled_arrival": (
                    delivery.scheduled_arrival
                ),

                "estimated_arrival": (
                    delivery.estimated_arrival
                ),

                "effective_arrival": (
                    arrival_time
                ),

                "dock_id": (
                    best_dock.id
                ),

                "yard_name": (
                    best_dock.yard_name
                ),

                "dock_number": (
                    best_dock.dock_number
                ),

                "dock_type": (
                    best_dock.dock_type
                ),

                "window_start": (
                    best_start_time
                ),

                "window_end": (
                    end_time
                ),

                "score": float(
                    best_score
                ),

                "reasons": (
                    best_reasons
                )
            }
        )

    # ========================================================
    # UNSCHEDULED TRAILERS
    # ========================================================

    unscheduled = []

    for delivery in deliveries:

        if (
            delivery.id
            not in scheduled_delivery_ids
        ):

            arrival_time = (
                get_effective_arrival(
                    delivery
                )
            )

            if arrival_time is None:

                reason = (
                    "No scheduled, estimated, "
                    "or actual arrival time"
                )

            else:

                reason = (
                    "No compatible usable dock found"
                )

            unscheduled.append(
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

                    "shipment_reference": (
                        delivery.shipment_reference
                    ),

                    "status": (
                        delivery.status
                    ),

                    "reason": (
                        reason
                    )
                }
            )

    # ========================================================
    # FINAL SCHEDULE
    # ========================================================

    return {
        "generated_at": (
            datetime.utcnow()
        ),

        "slot_duration_minutes": (
            DEFAULT_DOCK_SLOT_MINUTES
        ),

        "total_incoming_trailers": (
            len(deliveries)
        ),

        "total_docks": (
            len(docks)
        ),

        "scheduled_count": (
            len(schedule)
        ),

        "unscheduled_count": (
            len(unscheduled)
        ),

        "schedule": (
            schedule
        ),

        "unscheduled": (
            unscheduled
        )
    }


# ============================================================
# ASSIGN DOCK
# ============================================================

@router.post(
    "/assign/{delivery_id}",
    response_model=DeliveryResponse
)
def assign_dock(
    delivery_id: int,
    request: DockAssignmentRequest,
    db: Session = Depends(get_db)
):
    delivery = db.query(
        Delivery
    ).filter(
        Delivery.id == delivery_id
    ).first()

    if not delivery:

        raise HTTPException(
            status_code=404,
            detail="Delivery not found"
        )

    dock = db.query(
        YardDock
    ).filter(
        YardDock.id
        == request.dock_id
    ).first()

    if not dock:

        raise HTTPException(
            status_code=404,
            detail="Dock not found"
        )

    if dock.status != "available":

        raise HTTPException(
            status_code=400,
            detail=(
                "Dock is not available"
            )
        )

    # --------------------------------------------------------
    # RELEASE PREVIOUS RESERVATION
    # --------------------------------------------------------

    if (
        delivery.dock_id
        is not None
    ):

        old_dock = db.query(
            YardDock
        ).filter(
            YardDock.id
            == delivery.dock_id
        ).first()

        if (
            old_dock
            and old_dock.id != dock.id
            and old_dock.status
            == "reserved"
        ):

            old_dock.status = (
                "available"
            )

    # --------------------------------------------------------
    # ASSIGN
    # --------------------------------------------------------

    delivery.dock_id = (
        dock.id
    )

    dock.status = (
        "reserved"
    )

    if (
        delivery.status
        == "waiting_for_dock"
    ):

        delivery.status = (
            "dock_assigned"
        )

    db.commit()

    db.refresh(
        delivery
    )

    return delivery


# ============================================================
# MANUAL REASSIGN DOCK
# ============================================================

@router.post(
    "/reassign/{delivery_id}",
    response_model=DeliveryResponse
)
def reassign_dock(
    delivery_id: int,
    request: DockAssignmentRequest,
    db: Session = Depends(get_db)
):
    delivery = db.query(
        Delivery
    ).filter(
        Delivery.id == delivery_id
    ).first()

    if not delivery:

        raise HTTPException(
            status_code=404,
            detail="Delivery not found"
        )

    new_dock = db.query(
        YardDock
    ).filter(
        YardDock.id
        == request.dock_id
    ).first()

    if not new_dock:

        raise HTTPException(
            status_code=404,
            detail="New dock not found"
        )

    if (
        delivery.dock_id
        == new_dock.id
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Delivery is already assigned "
                "to this dock"
            )
        )

    if (
        new_dock.status
        != "available"
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "New dock is not available"
            )
        )

    old_dock = None

    if delivery.dock_id:

        old_dock = db.query(
            YardDock
        ).filter(
            YardDock.id
            == delivery.dock_id
        ).first()

        # Only release a normal reservation.
        # Blocked / maintenance / occupied state
        # must remain unchanged.
        if (
            old_dock
            and old_dock.status
            == "reserved"
        ):

            old_dock.status = (
                "available"
            )

    delivery.dock_id = (
        new_dock.id
    )

    new_dock.status = (
        "reserved"
    )

    if (
        delivery.status
        == "waiting_for_dock"
    ):

        delivery.status = (
            "dock_assigned"
        )

    db.commit()

    db.refresh(
        delivery
    )

    return delivery


# ============================================================
# AUTOMATIC DOCK REASSIGNMENT
# ============================================================

@router.post(
    "/auto-reassign/{delivery_id}",
    response_model=DeliveryResponse
)
def auto_reassign_dock(
    delivery_id: int,
    db: Session = Depends(get_db)
):
    """
    Automatically find and reserve the best compatible
    available replacement dock.

    The frontend does not need to provide a dock ID.
    """

    # ========================================================
    # DELIVERY
    # ========================================================

    delivery = db.query(
        Delivery
    ).filter(
        Delivery.id
        == delivery_id
    ).first()

    if not delivery:

        raise HTTPException(
            status_code=404,
            detail="Delivery not found"
        )

    # ========================================================
    # CURRENT DOCK
    # ========================================================

    old_dock = None

    if (
        delivery.dock_id
        is not None
    ):

        old_dock = db.query(
            YardDock
        ).filter(
            YardDock.id
            == delivery.dock_id
        ).first()

    # ========================================================
    # AVAILABLE REPLACEMENTS
    # ========================================================

    available_docks = db.query(
        YardDock
    ).filter(
        YardDock.status
        == "available"
    ).all()

    candidates = []

    for dock in available_docks:

        # Never select the current dock.
        if (
            old_dock is not None
            and dock.id
            == old_dock.id
        ):
            continue

        score, compatible, reasons = (
            calculate_dock_score(
                delivery,
                dock
            )
        )

        if not compatible:
            continue

        candidates.append(
            {
                "dock": (
                    dock
                ),

                "score": (
                    score
                ),

                "reasons": (
                    reasons
                )
            }
        )

    # ========================================================
    # NO REPLACEMENT
    # ========================================================

    if not candidates:

        raise HTTPException(
            status_code=409,

            detail={
                "message": (
                    "No compatible available dock "
                    "found for reassignment"
                ),

                "delivery_id": (
                    delivery.id
                ),

                "current_dock_id": (
                    delivery.dock_id
                )
            }
        )

    # ========================================================
    # SELECT HIGHEST SCORE
    # ========================================================

    candidates.sort(
        key=lambda item: (
            item["score"]
        ),
        reverse=True
    )

    selected = (
        candidates[0]
    )

    new_dock = (
        selected["dock"]
    )

    # ========================================================
    # RELEASE OLD RESERVATION ONLY
    # ========================================================

    if old_dock is not None:

        if (
            old_dock.status
            == "reserved"
        ):

            old_dock.status = (
                "available"
            )

    # ========================================================
    # ASSIGN NEW DOCK
    # ========================================================

    delivery.dock_id = (
        new_dock.id
    )

    new_dock.status = (
        "reserved"
    )

    if (
        delivery.status
        == "waiting_for_dock"
    ):

        delivery.status = (
            "dock_assigned"
        )

    db.commit()

    db.refresh(
        delivery
    )

    return delivery