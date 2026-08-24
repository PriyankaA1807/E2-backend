import math
import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Delivery, TrackingEvent


router = APIRouter(
    prefix="/simulation",
    tags=["GPS & Simulation"]
)


# ============================================================
# DISTANCE CALCULATION
# ============================================================

def calculate_distance_km(
    lat1,
    lon1,
    lat2,
    lon2
):
    if None in (
        lat1,
        lon1,
        lat2,
        lon2
    ):
        return None

    lat_distance = (lat2 - lat1) * 111

    lon_distance = (
        (lon2 - lon1)
        * 111
        * math.cos(math.radians(lat1))
    )

    return math.sqrt(
        lat_distance ** 2 +
        lon_distance ** 2
    )


# ============================================================
# START SIMULATION
# ============================================================

@router.post("/start/{delivery_id}")
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

    # Default starting coordinates
    if delivery.current_latitude is None:
        delivery.current_latitude = 22.5726
        delivery.current_longitude = 88.3639

    # Default destination coordinates
    if delivery.destination_latitude is None:
        delivery.destination_latitude = 23.0225
        delivery.destination_longitude = 72.5714

    delivery.simulation_active = True
    delivery.status = "in_transit"

    delivery.last_gps_update = datetime.utcnow()

    db.commit()

    return {
        "message": "GPS simulation started",
        "delivery_id": delivery_id,
        "status": delivery.status
    }


# ============================================================
# SIMULATE ONE MOVEMENT STEP
# ============================================================

@router.post("/step/{delivery_id}")
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
            detail="Simulation is not active"
        )

    if delivery.current_latitude is None:
        raise HTTPException(
            status_code=400,
            detail="Current GPS coordinates are missing"
        )

    if delivery.current_longitude is None:
        raise HTTPException(
            status_code=400,
            detail="Current GPS longitude is missing"
        )

    if delivery.destination_latitude is None:
        raise HTTPException(
            status_code=400,
            detail="Destination coordinates are missing"
        )

    if delivery.destination_longitude is None:
        raise HTTPException(
            status_code=400,
            detail="Destination longitude is missing"
        )

    old_lat = delivery.current_latitude
    old_lon = delivery.current_longitude

    destination_lat = delivery.destination_latitude
    destination_lon = delivery.destination_longitude

    # ========================================================
    # MOVE 5% TOWARD DESTINATION
    # ========================================================

    factor = 0.05

    new_lat = old_lat + (
        destination_lat - old_lat
    ) * factor

    new_lon = old_lon + (
        destination_lon - old_lon
    ) * factor

    # ========================================================
    # SMALL GPS VARIATION
    # ========================================================

    new_lat += random.uniform(
        -0.001,
        0.001
    )

    new_lon += random.uniform(
        -0.001,
        0.001
    )

    delivery.current_latitude = new_lat
    delivery.current_longitude = new_lon

    delivery.current_location = (
        f"{new_lat:.5f}, {new_lon:.5f}"
    )

    # ========================================================
    # RANDOM SPEED
    # ========================================================

    delivery.average_speed_kmph = random.uniform(
        35,
        65
    )

    # ========================================================
    # CALCULATE REMAINING DISTANCE
    # ========================================================

    distance = calculate_distance_km(
        new_lat,
        new_lon,
        destination_lat,
        destination_lon
    )

    delivery.distance_remaining_km = distance

    # ========================================================
    # ETA CALCULATION
    # ========================================================

    if distance is not None:

        delivery.eta_minutes = (
            distance /
            delivery.average_speed_kmph
        ) * 60

        delivery.estimated_arrival = (
            datetime.utcnow()
            + timedelta(
                minutes=delivery.eta_minutes
            )
        )

    delivery.last_gps_update = datetime.utcnow()

    # ========================================================
    # ARRIVAL DETECTION
    # ========================================================

    if distance is not None and distance < 2:

        delivery.status = "arrived"

        delivery.simulation_active = False

        delivery.actual_arrival = datetime.utcnow()

        # IMPORTANT:
        # Once arrived, there should be no remaining
        # distance or remaining ETA.

        delivery.distance_remaining_km = 0

        delivery.eta_minutes = 0

        delivery.estimated_arrival = (
            delivery.actual_arrival
        )

    # ========================================================
    # TRACKING EVENT
    # ========================================================

    event = TrackingEvent(
        delivery_id=delivery.id,
        status=delivery.status,
        location=delivery.current_location,
        latitude=new_lat,
        longitude=new_lon,
        description="Simulated GPS movement"
    )

    db.add(event)

    # ========================================================
    # SAVE
    # ========================================================

    db.commit()

    db.refresh(delivery)

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "delivery_id": delivery.id,
        "latitude": delivery.current_latitude,
        "longitude": delivery.current_longitude,
        "location": delivery.current_location,
        "distance_remaining_km": delivery.distance_remaining_km,
        "speed_kmph": delivery.average_speed_kmph,
        "eta_minutes": delivery.eta_minutes,
        "estimated_arrival": delivery.estimated_arrival,
        "status": delivery.status
    }


# ============================================================
# STOP SIMULATION
# ============================================================

@router.post("/stop/{delivery_id}")
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

    db.commit()

    return {
        "message": "GPS simulation stopped",
        "delivery_id": delivery_id
    }