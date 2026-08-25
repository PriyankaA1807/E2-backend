from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    Delivery,
    YardDock,
    RestockOrder,
    Inventory,
    Alert
)

from app.schemas import (
    YardStatusResponse,
    DockScheduleResponse,
    TrailerDoorAllocationResponse
)

from app.routers.dock_operations import (
    get_dock_schedule
)


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


# ============================================================
# ACTIVE DELIVERY STATUSES
# ============================================================

ACTIVE_DELIVERY_STATUSES = [
    "scheduled",
    "in_transit",
    "delayed",

    "arrived_at_gate",
    "in_yard",
    "waiting_for_dock",
    "dock_assigned",
    "docked",
    "unloading",

    # Legacy compatibility
    "arrived"
]


# ============================================================
# DASHBOARD SUMMARY
# ============================================================

@router.get("/summary")
def dashboard_summary(
    db: Session = Depends(get_db)
):

    total_shipments = db.query(
        Delivery
    ).count()

    active_shipments = db.query(
        Delivery
    ).filter(
        Delivery.status.in_(
            ACTIVE_DELIVERY_STATUSES
        )
    ).count()

    completed_shipments = db.query(
        Delivery
    ).filter(
        Delivery.status.in_([
            "completed",
            "departed",

            # Legacy compatibility
            "delivered"
        ])
    ).count()

    delayed_shipments = db.query(
        Delivery
    ).filter(
        Delivery.delay_detected == True
    ).count()

    exception_shipments = db.query(
        Delivery
    ).filter(
        Delivery.exception_detected == True
    ).count()

    total_docks = db.query(
        YardDock
    ).count()

    available_docks = db.query(
        YardDock
    ).filter(
        YardDock.status == "available"
    ).count()

    occupied_docks = db.query(
        YardDock
    ).filter(
        YardDock.status == "occupied"
    ).count()

    reserved_docks = db.query(
        YardDock
    ).filter(
        YardDock.status == "reserved"
    ).count()

    blocked_docks = db.query(
        YardDock
    ).filter(
        YardDock.status == "blocked"
    ).count()

    maintenance_docks = db.query(
        YardDock
    ).filter(
        YardDock.status == "maintenance"
    ).count()

    pending_orders = db.query(
        RestockOrder
    ).filter(
        RestockOrder.status == "pending"
    ).count()

    low_stock_items = 0

    inventory_items = db.query(
        Inventory
    ).all()

    for inventory in inventory_items:

        if inventory.product:

            if (
                inventory.current_stock
                <= inventory.product.reorder_level
            ):
                low_stock_items += 1

    active_alerts = db.query(
        Alert
    ).filter(
        Alert.resolved == False
    ).count()

    return {
        "shipments": {
            "total": total_shipments,
            "active": active_shipments,
            "completed": completed_shipments,
            "delayed": delayed_shipments,
            "exceptions": exception_shipments
        },

        "docks": {
            "total": total_docks,
            "available": available_docks,
            "occupied": occupied_docks,
            "reserved": reserved_docks,
            "blocked": blocked_docks,
            "maintenance": maintenance_docks
        },

        "inventory": {
            "low_stock_items": (
                low_stock_items
            ),

            "pending_restock_orders": (
                pending_orders
            )
        },

        "alerts": {
            "active": active_alerts
        }
    }


# ============================================================
# LIVE SHIPMENTS
# ============================================================

@router.get("/live-shipments")
def live_shipments(
    db: Session = Depends(get_db)
):

    shipments = db.query(
        Delivery
    ).filter(
        Delivery.status.in_(
            ACTIVE_DELIVERY_STATUSES
        )
    ).all()

    return [
        {
            "id": shipment.id,

            "tracking_number": (
                shipment.tracking_number
            ),

            "trailer_id": (
                shipment.trailer_id
            ),

            "shipment_reference": (
                shipment.shipment_reference
            ),

            "carrier": (
                shipment.carrier
            ),

            "status": (
                shipment.status
            ),

            "latitude": (
                shipment.current_latitude
            ),

            "longitude": (
                shipment.current_longitude
            ),

            "location": (
                shipment.current_location
            ),

            "eta_minutes": (
                shipment.eta_minutes
            ),

            "scheduled_arrival": (
                shipment.scheduled_arrival
            ),

            "estimated_arrival": (
                shipment.estimated_arrival
            ),

            "dock_id": (
                shipment.dock_id
            ),

            "delay_detected": (
                shipment.delay_detected
            ),

            "exception_detected": (
                shipment.exception_detected
            )
        }

        for shipment in shipments
    ]


# ============================================================
# DOCK STATUS
# ============================================================

@router.get("/dock-status")
def dock_status(
    db: Session = Depends(get_db)
):

    docks = db.query(
        YardDock
    ).all()

    return [
        {
            "id": dock.id,

            "yard_name": (
                dock.yard_name
            ),

            "dock_number": (
                dock.dock_number
            ),

            "status": (
                dock.status
            ),

            "dock_type": (
                dock.dock_type
            ),

            "supported_vehicle_type": (
                dock.supported_vehicle_type
            ),

            "max_vehicle_length": (
                dock.max_vehicle_length
            ),

            "refrigerated": (
                dock.refrigerated
            ),

            "hazardous_allowed": (
                dock.hazardous_allowed
            )
        }

        for dock in docks
    ]


# ============================================================
# YARD STATUS
# ============================================================

@router.get(
    "/yard-status",
    response_model=YardStatusResponse
)
def yard_status(
    db: Session = Depends(get_db)
):

    deliveries = db.query(
        Delivery
    ).filter(
        Delivery.status.in_(
            ACTIVE_DELIVERY_STATUSES
        )
    ).all()

    yard_items = []

    for delivery in deliveries:

        assigned_dock = None

        if delivery.dock_id is not None:

            dock = db.query(
                YardDock
            ).filter(
                YardDock.id
                == delivery.dock_id
            ).first()

            if dock:

                assigned_dock = {
                    "dock_id": dock.id,

                    "yard_name": (
                        dock.yard_name
                    ),

                    "dock_number": (
                        dock.dock_number
                    ),

                    "dock_status": (
                        dock.status
                    ),

                    "dock_type": (
                        dock.dock_type
                    )
                }

        if (
            delivery.status
            == "arrived_at_gate"
        ):

            operational_state = "AT_GATE"

        elif (
            delivery.status
            == "in_yard"
        ):

            operational_state = "IN_YARD"

        elif (
            delivery.status
            == "waiting_for_dock"
        ):

            operational_state = (
                "WAITING_FOR_DOCK"
            )

        elif (
            delivery.status
            == "dock_assigned"
        ):

            operational_state = (
                "DOCK_ASSIGNED"
            )

        elif (
            delivery.status
            == "docked"
        ):

            operational_state = "DOCKED"

        elif (
            delivery.status
            == "unloading"
        ):

            operational_state = "UNLOADING"

        elif (
            delivery.status
            == "delayed"
        ):

            operational_state = (
                "DELAYED_IN_TRANSIT"
            )

        elif (
            delivery.status
            == "in_transit"
        ):

            operational_state = (
                "IN_TRANSIT"
            )

        elif (
            delivery.status
            == "scheduled"
        ):

            operational_state = (
                "SCHEDULED"
            )

        elif (
            delivery.status
            == "arrived"
        ):

            operational_state = (
                "ARRIVED_LEGACY"
            )

        else:

            operational_state = (
                delivery.status.upper()
                if delivery.status
                else "UNKNOWN"
            )

        yard_items.append(
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

                "carrier": (
                    delivery.carrier
                ),

                "status": (
                    delivery.status
                ),

                "operational_state": (
                    operational_state
                ),

                "yard_location": (
                    delivery.current_location
                ),

                "current_latitude": (
                    delivery.current_latitude
                ),

                "current_longitude": (
                    delivery.current_longitude
                ),

                "scheduled_arrival": (
                    delivery.scheduled_arrival
                ),

                "estimated_arrival": (
                    delivery.estimated_arrival
                ),

                "actual_arrival": (
                    delivery.actual_arrival
                ),

                "eta_minutes": (
                    delivery.eta_minutes
                ),

                "distance_remaining_km": (
                    delivery.distance_remaining_km
                ),

                "delay_detected": (
                    delivery.delay_detected
                ),

                "exception_detected": (
                    delivery.exception_detected
                ),

                "assigned_dock": (
                    assigned_dock
                )
            }
        )

    at_gate = sum(
        1
        for item in yard_items
        if (
            item["operational_state"]
            == "AT_GATE"
        )
    )

    in_yard = sum(
        1
        for item in yard_items
        if (
            item["operational_state"]
            == "IN_YARD"
        )
    )

    waiting_for_dock = sum(
        1
        for item in yard_items
        if (
            item["operational_state"]
            == "WAITING_FOR_DOCK"
        )
    )

    dock_assigned = sum(
        1
        for item in yard_items
        if (
            item["operational_state"]
            == "DOCK_ASSIGNED"
        )
    )

    docked_or_unloading = sum(
        1
        for item in yard_items
        if (
            item["operational_state"]
            in {
                "DOCKED",
                "UNLOADING"
            }
        )
    )

    delayed = sum(
        1
        for item in yard_items
        if item["delay_detected"]
    )

    return {
        "summary": {
            "total_active_trailers": (
                len(yard_items)
            ),

            "at_gate": at_gate,

            "in_yard": in_yard,

            "waiting_for_dock": (
                waiting_for_dock
            ),

            "dock_assigned": (
                dock_assigned
            ),

            "docked_or_unloading": (
                docked_or_unloading
            ),

            "delayed": delayed
        },

        "trailers": yard_items
    }


# ============================================================
# DASHBOARD DOCK SCHEDULE
# ============================================================

@router.get(
    "/dock-schedule",
    response_model=DockScheduleResponse
)
def dashboard_dock_schedule(
    db: Session = Depends(get_db)
):

    return get_dock_schedule(
        db=db
    )


# ============================================================
# TRAILER TO DOOR ALLOCATION SUMMARY
# ============================================================

@router.get(
    "/trailer-door-allocation",
    response_model=TrailerDoorAllocationResponse
)
def trailer_door_allocation(
    db: Session = Depends(get_db)
):
    """
    Consolidated view of:

    - trailer
    - current dock
    - scheduled / recommended dock
    - arrival window
    - ETA
    - delay
    - exception
    - reassignment requirement
    """

    # --------------------------------------------------------
    # GET ACTIVE TRAILERS
    # --------------------------------------------------------

    deliveries = db.query(
        Delivery
    ).filter(
        Delivery.status.in_(
            ACTIVE_DELIVERY_STATUSES
        )
    ).all()

    # --------------------------------------------------------
    # REUSE CENTRAL SCHEDULER
    # --------------------------------------------------------

    schedule_result = (
        get_dock_schedule(
            db=db
        )
    )

    schedule_by_delivery = {}

    for schedule_item in (
        schedule_result["schedule"]
    ):

        schedule_by_delivery[
            schedule_item["delivery_id"]
        ] = schedule_item

    # --------------------------------------------------------
    # DOCK STATES THAT REQUIRE REASSIGNMENT
    # --------------------------------------------------------

    unavailable_dock_statuses = {
        "blocked",
        "maintenance",
        "occupied"
    }

    allocations = []

    currently_assigned_count = 0
    assignment_recommended_count = 0
    reassignment_required_count = 0
    unscheduled_count = 0
    delayed_count = 0

    # --------------------------------------------------------
    # BUILD ALLOCATION FOR EACH TRAILER
    # --------------------------------------------------------

    for delivery in deliveries:

        current_dock_data = None
        current_dock = None

        # ----------------------------------------------------
        # CURRENT DOCK
        # ----------------------------------------------------

        if (
            delivery.dock_id
            is not None
        ):

            current_dock = db.query(
                YardDock
            ).filter(
                YardDock.id
                == delivery.dock_id
            ).first()

            if current_dock:

                current_dock_data = {
                    "dock_id": (
                        current_dock.id
                    ),

                    "yard_name": (
                        current_dock.yard_name
                    ),

                    "dock_number": (
                        current_dock.dock_number
                    ),

                    "dock_status": (
                        current_dock.status
                    ),

                    "dock_type": (
                        current_dock.dock_type
                    )
                }

        # ----------------------------------------------------
        # SCHEDULED / RECOMMENDED DOCK
        # ----------------------------------------------------

        schedule_item = (
            schedule_by_delivery.get(
                delivery.id
            )
        )

        scheduled_dock_data = None

        if schedule_item:

            scheduled_dock_data = {
                "dock_id": (
                    schedule_item[
                        "dock_id"
                    ]
                ),

                "yard_name": (
                    schedule_item[
                        "yard_name"
                    ]
                ),

                "dock_number": (
                    schedule_item[
                        "dock_number"
                    ]
                ),

                "dock_type": (
                    schedule_item[
                        "dock_type"
                    ]
                ),

                "window_start": (
                    schedule_item[
                        "window_start"
                    ]
                ),

                "window_end": (
                    schedule_item[
                        "window_end"
                    ]
                ),

                "score": (
                    schedule_item[
                        "score"
                    ]
                ),

                "reasons": (
                    schedule_item[
                        "reasons"
                    ]
                )
            }

        # ----------------------------------------------------
        # REASSIGNMENT REQUIRED?
        # ----------------------------------------------------

        reassignment_required = False

        if current_dock is not None:

            if (
                current_dock.status
                in unavailable_dock_statuses
            ):

                reassignment_required = True

        # ----------------------------------------------------
        # ALLOCATION STATUS
        # ----------------------------------------------------

        allocation_status = (
            "UNSCHEDULED"
        )

        if (
            reassignment_required
            and schedule_item is not None
            and (
                current_dock is None
                or schedule_item["dock_id"]
                != current_dock.id
            )
        ):

            allocation_status = (
                "REASSIGNMENT_RECOMMENDED"
            )

            reassignment_required_count += 1

        elif (
            delivery.dock_id is None
            and schedule_item is not None
        ):

            allocation_status = (
                "ASSIGNMENT_RECOMMENDED"
            )

            assignment_recommended_count += 1

        elif (
            current_dock is not None
            and schedule_item is not None
            and schedule_item["dock_id"]
            == current_dock.id
            and not reassignment_required
        ):

            allocation_status = (
                "CURRENT_ASSIGNMENT_VALID"
            )

            currently_assigned_count += 1

        elif (
            reassignment_required
            and schedule_item is None
        ):

            allocation_status = (
                "REASSIGNMENT_REQUIRED_NO_DOCK"
            )

            reassignment_required_count += 1

        elif (
            current_dock is not None
            and not reassignment_required
        ):

            allocation_status = (
                "CURRENTLY_ASSIGNED"
            )

            currently_assigned_count += 1

        else:

            unscheduled_count += 1

        # ----------------------------------------------------
        # DELAY
        # ----------------------------------------------------

        if delivery.delay_detected:
            delayed_count += 1

        # ----------------------------------------------------
        # ADD TO RESPONSE
        # ----------------------------------------------------

        allocations.append(
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

                "carrier": (
                    delivery.carrier
                ),

                "delivery_status": (
                    delivery.status
                ),

                "scheduled_arrival": (
                    delivery.scheduled_arrival
                ),

                "estimated_arrival": (
                    delivery.estimated_arrival
                ),

                "actual_arrival": (
                    delivery.actual_arrival
                ),

                "eta_minutes": (
                    delivery.eta_minutes
                ),

                "delay_detected": (
                    delivery.delay_detected
                ),

                "exception_detected": (
                    delivery.exception_detected
                ),

                "current_dock": (
                    current_dock_data
                ),

                "scheduled_dock": (
                    scheduled_dock_data
                ),

                "reassignment_required": (
                    reassignment_required
                ),

                "allocation_status": (
                    allocation_status
                )
            }
        )

    # --------------------------------------------------------
    # FINAL RESPONSE
    # --------------------------------------------------------

    return {
        "generated_at": (
            datetime.utcnow()
        ),

        "summary": {
            "total_trailers": (
                len(allocations)
            ),

            "currently_assigned": (
                currently_assigned_count
            ),

            "assignment_recommended": (
                assignment_recommended_count
            ),

            "reassignment_required": (
                reassignment_required_count
            ),

            "unscheduled": (
                unscheduled_count
            ),

            "delayed": (
                delayed_count
            )
        },

        "allocations": (
            allocations
        )
    }


# ============================================================
# OPERATIONAL INSIGHTS
# ============================================================

@router.get("/insights")
def operational_insights(
    db: Session = Depends(get_db)
):

    insights = []

    delayed = db.query(
        Delivery
    ).filter(
        Delivery.delay_detected
        == True
    ).count()

    available = db.query(
        YardDock
    ).filter(
        YardDock.status
        == "available"
    ).count()

    blocked = db.query(
        YardDock
    ).filter(
        YardDock.status
        == "blocked"
    ).count()

    maintenance = db.query(
        YardDock
    ).filter(
        YardDock.status
        == "maintenance"
    ).count()

    active_alerts = db.query(
        Alert
    ).filter(
        Alert.resolved
        == False
    ).count()

    if delayed > 0:

        insights.append(
            {
                "type": "delay",

                "priority": "high",

                "message": (
                    f"{delayed} shipment(s) are "
                    "delayed. Review ETA and "
                    "dock allocation."
                )
            }
        )

    if available == 0:

        insights.append(
            {
                "type": "dock_capacity",

                "priority": "high",

                "message": (
                    "No docks are currently "
                    "available. Consider dock "
                    "reassignment."
                )
            }
        )

    elif available <= 2:

        insights.append(
            {
                "type": "dock_capacity",

                "priority": "medium",

                "message": (
                    "Dock availability is "
                    "becoming limited."
                )
            }
        )

    if blocked > 0:

        insights.append(
            {
                "type": "dock_blocked",

                "priority": "high",

                "message": (
                    f"{blocked} dock(s) are "
                    "currently blocked."
                )
            }
        )

    if maintenance > 0:

        insights.append(
            {
                "type": "dock_maintenance",

                "priority": "medium",

                "message": (
                    f"{maintenance} dock(s) are "
                    "currently under maintenance."
                )
            }
        )

    if active_alerts > 0:

        insights.append(
            {
                "type": "alerts",

                "priority": "high",

                "message": (
                    f"There are {active_alerts} "
                    "unresolved operational alerts."
                )
            }
        )

    if not insights:

        insights.append(
            {
                "type": "system",

                "priority": "low",

                "message": (
                    "Operations are currently "
                    "running normally."
                )
            }
        )

    return {
        "insights": (
            insights
        ),

        "count": (
            len(insights)
        )
    }