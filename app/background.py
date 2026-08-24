import asyncio
from datetime import datetime, timedelta

from app.database import SessionLocal
from app.models import Delivery


async def tracking_background_loop():

    while True:

        db = None

        try:
            db = SessionLocal()

            deliveries = (
                db.query(Delivery)
                .filter(Delivery.simulation_active == True)
                .all()
            )

            for delivery in deliveries:

                # Skip delivery if required GPS data is missing
                if (
                    delivery.current_latitude is None
                    or delivery.current_longitude is None
                    or delivery.destination_latitude is None
                    or delivery.destination_longitude is None
                ):
                    continue

                # =====================================================
                # MOVE TOWARD DESTINATION
                # =====================================================

                factor = 0.02

                delivery.current_latitude += (
                    delivery.destination_latitude
                    - delivery.current_latitude
                ) * factor

                delivery.current_longitude += (
                    delivery.destination_longitude
                    - delivery.current_longitude
                ) * factor

                # Background simulation speed
                delivery.average_speed_kmph = 50

                delivery.last_gps_update = datetime.utcnow()

                # =====================================================
                # DISTANCE CALCULATION
                # =====================================================

                lat_difference = abs(
                    delivery.destination_latitude
                    - delivery.current_latitude
                )

                lon_difference = abs(
                    delivery.destination_longitude
                    - delivery.current_longitude
                )

                distance = (
                    lat_difference
                    + lon_difference
                ) * 111

                delivery.distance_remaining_km = distance

                # =====================================================
                # ETA CALCULATION
                # =====================================================

                delivery.eta_minutes = (
                    distance
                    / delivery.average_speed_kmph
                ) * 60

                delivery.estimated_arrival = (
                    datetime.utcnow()
                    + timedelta(
                        minutes=delivery.eta_minutes
                    )
                )

                # =====================================================
                # ARRIVAL DETECTION
                # =====================================================

                if distance < 1:

                    delivery.status = "arrived"

                    delivery.simulation_active = False

                    delivery.actual_arrival = datetime.utcnow()

                    # Once arrived, no distance or ETA remains
                    delivery.distance_remaining_km = 0

                    delivery.eta_minutes = 0

                    delivery.estimated_arrival = (
                        delivery.actual_arrival
                    )

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

        await asyncio.sleep(10)