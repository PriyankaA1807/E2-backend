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


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


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
        Delivery.status.in_([
            "scheduled",
            "in_transit",
            "delayed",
            "arrived",
            "unloading"
        ])
    ).count()

    delivered_shipments = db.query(
        Delivery
    ).filter(
        Delivery.status == "delivered"
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
            "delivered": delivered_shipments,
            "delayed": delayed_shipments,
            "exceptions": exception_shipments
        },
        "docks": {
            "total": total_docks,
            "available": available_docks,
            "occupied": occupied_docks,
            "reserved": reserved_docks
        },
        "inventory": {
            "low_stock_items": low_stock_items,
            "pending_restock_orders": pending_orders
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
        Delivery.status.in_([
            "scheduled",
            "in_transit",
            "delayed",
            "arrived",
            "unloading"
        ])
    ).all()

    return [
        {
            "id": shipment.id,
            "tracking_number": shipment.tracking_number,
            "carrier": shipment.carrier,
            "status": shipment.status,
            "latitude": shipment.current_latitude,
            "longitude": shipment.current_longitude,
            "location": shipment.current_location,
            "eta_minutes": shipment.eta_minutes,
            "estimated_arrival": shipment.estimated_arrival,
            "delay_detected": shipment.delay_detected,
            "exception_detected": shipment.exception_detected
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
            "yard_name": dock.yard_name,
            "dock_number": dock.dock_number,
            "status": dock.status,
            "dock_type": dock.dock_type,
            "refrigerated": dock.refrigerated,
            "hazardous_allowed": dock.hazardous_allowed
        }
        for dock in docks
    ]


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
        Delivery.delay_detected == True
    ).count()

    available = db.query(
        YardDock
    ).filter(
        YardDock.status == "available"
    ).count()

    active_alerts = db.query(
        Alert
    ).filter(
        Alert.resolved == False
    ).count()

    if delayed > 0:

        insights.append({
            "type": "delay",
            "priority": "high",
            "message": (
                f"{delayed} shipment(s) are delayed. "
                "Review ETA and dock allocation."
            )
        })

    if available == 0:

        insights.append({
            "type": "dock_capacity",
            "priority": "high",
            "message": (
                "No docks are currently available. "
                "Consider reassignment or yard expansion."
            )
        })

    elif available <= 2:

        insights.append({
            "type": "dock_capacity",
            "priority": "medium",
            "message": (
                "Dock availability is becoming limited."
            )
        })

    if active_alerts > 0:

        insights.append({
            "type": "alerts",
            "priority": "high",
            "message": (
                f"There are {active_alerts} unresolved "
                "operational alerts."
            )
        })

    if not insights:

        insights.append({
            "type": "system",
            "priority": "low",
            "message": (
                "Operations are currently running normally."
            )
        })

    return {
        "insights": insights,
        "count": len(insights)
    }