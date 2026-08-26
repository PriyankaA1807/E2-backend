import asyncio
import math
from datetime import datetime

from app.database import SessionLocal
from app.models import Delivery, TrackingEvent, Alert
from app.ml.eta import predict_eta


# ============================================================
# HAVERSINE DISTANCE
# ============================================================

def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float
) -> float:
    """
    Calculate the geographical distance between two
    latitude/longitude points in kilometers.
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
# MOVE TRUCK TOWARDS DESTINATION
# ============================================================

def move_towards_destination(
    current_lat: float,
    current_lon: float,
    destination_lat: float,
    destination_lon: float,
    progress_ratio: float = 0.15
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
# BACKGROUND TRACKING LOOP
# ============================================================

async def tracking_background_loop():

    while True:

        db = None

        try:
            db = SessionLocal()

            # --------------------------------------------------------
            # Get only deliveries whose simulation is active
            # --------------------------------------------------------

            deliveries = (
                db.query(Delivery)
                .filter(
                    Delivery.simulation_active == True
                )
                .all()
            )

            for delivery in deliveries:

                # ====================================================
                # CHECK REQUIRED GPS DATA
                # ====================================================

                if (
                    delivery.current_latitude is None
                    or delivery.current_longitude is None
                    or delivery.destination_latitude is None
                    or delivery.destination_longitude is None
                ):
                    continue

                now = datetime.utcnow()

                # ====================================================
                # CALCULATE CURRENT DISTANCE
                # ====================================================

                current_distance = haversine_distance(
                    delivery.current_latitude,
                    delivery.current_longitude,
                    delivery.destination_latitude,
                    delivery.destination_longitude
                )

                # ====================================================
                # ARRIVAL DETECTION
                # ====================================================

                if current_distance <= 2.0:

                    # Snap truck exactly to warehouse / yard gate
                    delivery.current_latitude = (
                        delivery.destination_latitude
                    )

                    delivery.current_longitude = (
                        delivery.destination_longitude
                    )

                    delivery.current_location = "Yard Gate"

                    # Final arrival state
                    delivery.status = "arrived_at_gate"

                    delivery.simulation_active = False

                    delivery.actual_arrival = now

                    delivery.last_gps_update = now

                    # No remaining journey
                    delivery.distance_remaining_km = 0.0
                    delivery.eta_minutes = 0.0
                    delivery.estimated_arrival = now

                    # ------------------------------------------------
                    # Save final tracking event
                    # ------------------------------------------------

                    event = TrackingEvent(
                        delivery_id=delivery.id,
                        status="arrived_at_gate",
                        location="Yard Gate",
                        latitude=(
                            delivery.current_latitude
                        ),
                        longitude=(
                            delivery.current_longitude
                        ),
                        event_time=now,
                        description=(
                            "Truck arrived at yard gate during "
                            "automatic GPS simulation"
                        )
                    )

                    db.add(event)

                    continue

                # ====================================================
                # MOVE TRUCK
                # ====================================================

                new_lat, new_lon = move_towards_destination(
                    current_lat=delivery.current_latitude,
                    current_lon=delivery.current_longitude,
                    destination_lat=(
                        delivery.destination_latitude
                    ),
                    destination_lon=(
                        delivery.destination_longitude
                    ),
                    progress_ratio=0.15
                )

                delivery.current_latitude = new_lat
                delivery.current_longitude = new_lon

                delivery.current_location = (
                    f"{new_lat:.5f}, {new_lon:.5f}"
                )

                delivery.last_gps_update = now

                # ====================================================
                # CALCULATE NEW REMAINING DISTANCE
                # ====================================================

                remaining_distance = haversine_distance(
                    new_lat,
                    new_lon,
                    delivery.destination_latitude,
                    delivery.destination_longitude
                )

                delivery.distance_remaining_km = (
                    remaining_distance
                )

                # ====================================================
                # GET SHIPMENT QUANTITY
                # ====================================================

                quantity = 1.0

                if (
                    delivery.restock_order
                    and delivery.restock_order.quantity
                    and delivery.restock_order.quantity > 0
                ):
                    quantity = float(
                        delivery.restock_order.quantity
                    )

                # ====================================================
                # RANDOM FOREST ETA PREDICTION
                # ====================================================

                prediction = predict_eta(
                    distance_km=remaining_distance,
                    quantity=quantity,
                    supplier_delay_history=0.0,
                    carrier_delay_history=0.0
                )

                delivery.eta_minutes = (
                    prediction[
                        "estimated_delivery_minutes"
                    ]
                )

                delivery.estimated_arrival = (
                    prediction[
                        "estimated_arrival"
                    ]
                )

                # ====================================================
                # STATUS
                # ====================================================

                if delivery.status == "scheduled":
                    delivery.status = "in_transit"

                # ====================================================
                # DELAY DETECTION
                # ====================================================

                delay_threshold_minutes = 15.0

                if delivery.scheduled_arrival is not None:

                    predicted_delay_minutes = max(
                        0.0,
                        (
                            delivery.estimated_arrival
                            - delivery.scheduled_arrival
                        ).total_seconds()
                        / 60
                    )

                    # ------------------------------------------------
                    # Delay detected
                    # ------------------------------------------------

                    if (
                        predicted_delay_minutes
                        > delay_threshold_minutes
                    ):

                        delivery.delay_detected = True

                        if delivery.status in {
                            "scheduled",
                            "in_transit"
                        }:
                            delivery.status = "delayed"

                        # --------------------------------------------
                        # Avoid duplicate unresolved delay alerts
                        # --------------------------------------------

                        existing_alert = (
                            db.query(Alert)
                            .filter(
                                Alert.delivery_id
                                == delivery.id,

                                Alert.alert_type
                                == "delay",

                                Alert.resolved
                                == False
                            )
                            .first()
                        )

                        if not existing_alert:

                            trailer_label = (
                                delivery.trailer_id
                                or delivery.tracking_number
                                or f"delivery {delivery.id}"
                            )

                            alert = Alert(
                                delivery_id=delivery.id,
                                alert_type="delay",
                                severity="high",
                                title=(
                                    "Predicted Shipment Delay"
                                ),
                                message=(
                                    f"Trailer {trailer_label} "
                                    f"is predicted to arrive "
                                    f"{predicted_delay_minutes:.1f} "
                                    "minutes late."
                                )
                            )

                            db.add(alert)

                    else:
                        # Prediction is no longer over threshold
                        delivery.delay_detected = False

                        if delivery.status == "delayed":
                            delivery.status = "in_transit"

                # ====================================================
                # SAVE AUTOMATIC GPS EVENT
                # ====================================================

                event = TrackingEvent(
                    delivery_id=delivery.id,
                    status=delivery.status,
                    location=delivery.current_location,
                    latitude=new_lat,
                    longitude=new_lon,
                    event_time=now,
                    description=(
                        "Automatic simulated GPS update "
                        "with Random Forest ETA"
                    )
                )

                db.add(event)

            db.commit()

        except Exception as e:

            print(
                f"Background tracking error: {e}"
            )

            if db:
                db.rollback()

        finally:

            if db:
                db.close()

        # ============================================================
        # UPDATE ACTIVE TRUCKS EVERY 3 SECONDS
        # ============================================================

        await asyncio.sleep(3)