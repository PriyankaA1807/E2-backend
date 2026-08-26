from datetime import datetime, timedelta
import math
import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Delivery, TrackingEvent, YardDock
from app.schemas import (
    WMSFeedResponse,
    SimulationStartResponse,
    SimulationStepResponse,
    SimulationStopResponse,
)


router = APIRouter(
    prefix="/simulation",
    tags=["GPS & Simulation"]
)


# ============================================================
# HELPER: HAVERSINE DISTANCE
# ============================================================

def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calculate distance between two latitude/longitude points
    in kilometers.
    """

    radius_earth_km = 6371.0

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(delta_lon / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return radius_earth_km * c


# ============================================================
# HELPER: MOVE POINT TOWARDS DESTINATION
# ============================================================

def move_towards_destination(
    current_lat: float,
    current_lon: float,
    destination_lat: float,
    destination_lon: float,
    progress_ratio: float = 0.08
):
    """
    Move the simulated truck a fraction of the remaining
    distance toward the destination.
    """

    new_lat = current_lat + (
        destination_lat - current_lat
    ) * progress_ratio

    new_lon = current_lon + (
        destination_lon - current_lon
    ) * progress_ratio

    return new_lat, new_lon


# ============================================================
# START GPS SIMULATION
# ============================================================

@router.post(
    "/start/{delivery_id}",
    response_model=SimulationStartResponse
)
def start_simulation(
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

    if (
        delivery.destination_latitude is None
        or delivery.destination_longitude is None
    ):
        raise HTTPException(
            status_code=400,
            detail="Destination coordinates are required"
        )

    # If this delivery already completed/arrived in an earlier
    # simulation, generate a fresh starting location.
    finished_statuses = {
        "arrived_at_gate",
        "in_yard",
        "waiting_for_dock",
        "dock_assigned",
        "docked",
        "unloading",
        "arrived",
        "completed",
        "departed"
    }

    if (
        delivery.current_latitude is None
        or delivery.current_longitude is None
        or delivery.status in finished_statuses
    ):
        delivery.current_latitude = (
            delivery.destination_latitude
            + random.uniform(2.0, 8.0)
        )

        delivery.current_longitude = (
            delivery.destination_longitude
            + random.uniform(2.0, 8.0)
        )

    # Starting/restarting simulation means the truck is travelling.
    delivery.simulation_active = True
    delivery.status = "in_transit"

    # Clear stale state from an earlier run.
    delivery.actual_arrival = None
    delivery.delay_detected = False
    delivery.exception_detected = False
    delivery.last_gps_update = datetime.utcnow()

    delivery.current_location = (
        f"{delivery.current_latitude:.5f}, "
        f"{delivery.current_longitude:.5f}"
    )

    distance = haversine_distance(
        delivery.current_latitude,
        delivery.current_longitude,
        delivery.destination_latitude,
        delivery.destination_longitude
    )

    delivery.distance_remaining_km = distance

    speed = (
        delivery.average_speed_kmph
        if (
            delivery.average_speed_kmph
            and delivery.average_speed_kmph > 0
        )
        else 50.0
    )

    eta_minutes = (distance / speed) * 60

    delivery.eta_minutes = eta_minutes

    delivery.estimated_arrival = (
        datetime.utcnow()
        + timedelta(minutes=eta_minutes)
    )

    event = TrackingEvent(
        delivery_id=delivery.id,
        status="in_transit",
        location=delivery.current_location,
        latitude=delivery.current_latitude,
        longitude=delivery.current_longitude,
        event_time=datetime.utcnow(),
        description="GPS simulation started"
    )

    db.add(event)
    db.commit()
    db.refresh(delivery)

    return {
        "message": "Simulation started",
        "delivery_id": delivery.id,
        "tracking_number": delivery.tracking_number,
        "trailer_id": delivery.trailer_id,
        "status": delivery.status,
        "simulation_active": delivery.simulation_active,
        "current_latitude": delivery.current_latitude,
        "current_longitude": delivery.current_longitude,
        "current_location": delivery.current_location,
        "distance_remaining_km": delivery.distance_remaining_km,
        "eta_minutes": delivery.eta_minutes,
        "estimated_arrival": delivery.estimated_arrival
    }


# ============================================================
# SIMULATE ONE GPS STEP
# ============================================================

@router.post(
    "/step/{delivery_id}",
    response_model=SimulationStepResponse
)
def simulate_step(
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

    if not delivery.simulation_active:
        raise HTTPException(
            status_code=400,
            detail="Simulation is not active for this delivery"
        )

    if (
        delivery.current_latitude is None
        or delivery.current_longitude is None
        or delivery.destination_latitude is None
        or delivery.destination_longitude is None
    ):
        raise HTTPException(
            status_code=400,
            detail="Current and destination coordinates are required"
        )

    current_distance = haversine_distance(
        delivery.current_latitude,
        delivery.current_longitude,
        delivery.destination_latitude,
        delivery.destination_longitude
    )

    # --------------------------------------------------------
    # ARRIVAL CONDITION
    # --------------------------------------------------------

    if current_distance <= 2.0:
        delivery.current_latitude = (
            delivery.destination_latitude
        )

        delivery.current_longitude = (
            delivery.destination_longitude
        )

        delivery.current_location = "Yard Gate"

        delivery.distance_remaining_km = 0
        delivery.eta_minutes = 0
        delivery.estimated_arrival = datetime.utcnow()
        delivery.actual_arrival = datetime.utcnow()

        delivery.status = "arrived_at_gate"
        delivery.simulation_active = False
        delivery.last_gps_update = datetime.utcnow()

        event = TrackingEvent(
            delivery_id=delivery.id,
            status="arrived_at_gate",
            location="Yard Gate",
            latitude=delivery.current_latitude,
            longitude=delivery.current_longitude,
            event_time=datetime.utcnow(),
            description="Truck arrived at yard gate"
        )

        db.add(event)
        db.commit()
        db.refresh(delivery)

        return {
            "message": "Truck arrived at yard gate",
            "delivery_id": delivery.id,
            "status": delivery.status,
            "simulation_active": False,
            "current_latitude": delivery.current_latitude,
            "current_longitude": delivery.current_longitude,
            "distance_remaining_km": 0,
            "eta_minutes": 0
        }

    # --------------------------------------------------------
    # SIMULATE MOVEMENT
    # --------------------------------------------------------

    new_lat, new_lon = move_towards_destination(
        delivery.current_latitude,
        delivery.current_longitude,
        delivery.destination_latitude,
        delivery.destination_longitude,
        progress_ratio=random.uniform(0.05, 0.12)
    )

    delivery.current_latitude = new_lat
    delivery.current_longitude = new_lon

    delivery.current_location = (
        f"{new_lat:.5f}, {new_lon:.5f}"
    )

    delivery.last_gps_update = datetime.utcnow()

    # Simulate changing road speed.
    simulated_speed = random.uniform(
        35.0,
        70.0
    )

    delivery.average_speed_kmph = simulated_speed

    remaining_distance = haversine_distance(
        new_lat,
        new_lon,
        delivery.destination_latitude,
        delivery.destination_longitude
    )

    delivery.distance_remaining_km = remaining_distance

    eta_minutes = (
        remaining_distance
        / simulated_speed
    ) * 60

    delivery.eta_minutes = eta_minutes

    delivery.estimated_arrival = (
        datetime.utcnow()
        + timedelta(minutes=eta_minutes)
    )

    if delivery.status == "scheduled":
        delivery.status = "in_transit"

    event = TrackingEvent(
        delivery_id=delivery.id,
        status=delivery.status,
        location=delivery.current_location,
        latitude=new_lat,
        longitude=new_lon,
        event_time=datetime.utcnow(),
        description="Simulated GPS location update"
    )

    db.add(event)
    db.commit()
    db.refresh(delivery)

    return {
        "message": "Simulation step completed",
        "delivery_id": delivery.id,
        "tracking_number": delivery.tracking_number,
        "trailer_id": delivery.trailer_id,
        "status": delivery.status,
        "current_latitude": delivery.current_latitude,
        "current_longitude": delivery.current_longitude,
        "current_location": delivery.current_location,
        "average_speed_kmph": (
            delivery.average_speed_kmph
        ),
        "distance_remaining_km": (
            delivery.distance_remaining_km
        ),
        "eta_minutes": delivery.eta_minutes,
        "estimated_arrival": (
            delivery.estimated_arrival
        ),
        "simulation_active": (
            delivery.simulation_active
        )
    }


# ============================================================
# STOP GPS SIMULATION
# ============================================================

@router.post(
    "/stop/{delivery_id}",
    response_model=SimulationStopResponse
)
def stop_simulation(
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

    delivery.simulation_active = False

    event = TrackingEvent(
        delivery_id=delivery.id,
        status=delivery.status,
        location=delivery.current_location,
        latitude=delivery.current_latitude,
        longitude=delivery.current_longitude,
        event_time=datetime.utcnow(),
        description="GPS simulation stopped"
    )

    db.add(event)
    db.commit()
    db.refresh(delivery)

    return {
        "message": "Simulation stopped",
        "delivery_id": delivery.id,
        "status": delivery.status,
        "simulation_active": False
    }


# ============================================================
# SIMULATED WMS FEED
# ============================================================

@router.get(
    "/wms-feed",
    response_model=WMSFeedResponse
)
def get_wms_feed(
    db: Session = Depends(get_db)
):
    """
    Simulated Warehouse Management System feed.

    Returns current trailer/shipment information together
    with yard and dock-door availability.
    """

    deliveries = db.query(Delivery).all()
    docks = db.query(YardDock).all()

    # --------------------------------------------------------
    # TRAILER / SHIPMENT FEED
    # --------------------------------------------------------

    trailer_feed = []

    for delivery in deliveries:

        assigned_dock = None

        if delivery.dock is not None:
            assigned_dock = {
                "dock_id": delivery.dock.id,
                "dock_number": (
                    delivery.dock.dock_number
                ),
                "yard_name": (
                    delivery.dock.yard_name
                ),
                "status": delivery.dock.status,
                "dock_type": (
                    delivery.dock.dock_type
                )
            }

        trailer_feed.append(
            {
                "delivery_id": delivery.id,

                "tracking_number": (
                    delivery.tracking_number
                ),

                "trailer_id": delivery.trailer_id,

                "shipment_reference": (
                    delivery.shipment_reference
                ),

                "carrier": delivery.carrier,

                "trailer_status": delivery.status,

                "yard_location": (
                    delivery.current_location
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

                "current_latitude": (
                    delivery.current_latitude
                ),

                "current_longitude": (
                    delivery.current_longitude
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

                "simulation_active": (
                    delivery.simulation_active
                ),

                "assigned_dock": assigned_dock
            }
        )

    # --------------------------------------------------------
    # DOCK FEED
    # --------------------------------------------------------

    dock_feed = []

    for dock in docks:
        dock_feed.append(
            {
                "dock_id": dock.id,
                "yard_name": dock.yard_name,
                "dock_number": dock.dock_number,
                "status": dock.status,
                "dock_type": dock.dock_type,

                "supported_vehicle_type": (
                    getattr(
                        dock,
                        "supported_vehicle_type",
                        None
                    )
                ),

                "max_vehicle_length": (
                    getattr(
                        dock,
                        "max_vehicle_length",
                        None
                    )
                ),

                "refrigerated": (
                    getattr(
                        dock,
                        "refrigerated",
                        None
                    )
                ),

                "hazardous_allowed": (
                    getattr(
                        dock,
                        "hazardous_allowed",
                        None
                    )
                )
            }
        )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    available_docks = sum(
        1
        for dock in docks
        if (
            dock.status
            and dock.status.lower() == "available"
        )
    )

    inactive_statuses = {
        "completed",
        "departed",
        "cancelled"
    }

    active_shipments = sum(
        1
        for delivery in deliveries
        if (
            delivery.status
            and delivery.status.lower()
            not in inactive_statuses
        )
    )

    delayed_shipments = sum(
        1
        for delivery in deliveries
        if delivery.delay_detected
    )

    waiting_for_dock = sum(
        1
        for delivery in deliveries
        if delivery.status == "waiting_for_dock"
    )

    return {
        "feed_type": "SIMULATED_WMS",

        "generated_at": datetime.utcnow(),

        "summary": {
            "total_trailers": len(deliveries),
            "active_shipments": active_shipments,
            "delayed_shipments": delayed_shipments,
            "waiting_for_dock": waiting_for_dock,
            "total_docks": len(docks),
            "available_docks": available_docks
        },

        "trailers": trailer_feed,

        "docks": dock_feed
    }