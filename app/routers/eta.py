from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query
)

from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    Delivery,
    RestockOrder,
    Alert
)

from app.ml.eta import predict_eta

from app.schemas import (
    DeliveryETAPredictionResponse
)


router = APIRouter(
    prefix="/eta",
    tags=["ETA"]
)


# ============================================================
# BASIC / STANDALONE ETA PREDICTION
# ============================================================

@router.get("/predict")
def get_eta(
    distance_km: float,
    quantity: float,
    supplier_delay_history: float,
    carrier_delay_history: float
):
    """
    Standalone ETA prediction.

    This endpoint allows direct testing of the
    RandomForestRegressor without requiring a delivery ID.
    """

    try:

        result = predict_eta(
            distance_km=distance_km,
            quantity=quantity,
            supplier_delay_history=(
                supplier_delay_history
            ),
            carrier_delay_history=(
                carrier_delay_history
            )
        )

        return result

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc)
        )


# ============================================================
# DELIVERY-AWARE ETA PREDICTION
# ============================================================

@router.post(
    "/predict-delivery/{delivery_id}",
    response_model=DeliveryETAPredictionResponse
)
def predict_delivery_eta(
    delivery_id: int,

    supplier_delay_history: float = Query(
        default=0.0,
        ge=0
    ),

    carrier_delay_history: float = Query(
        default=0.0,
        ge=0
    ),

    delay_threshold_minutes: float = Query(
        default=15.0,
        ge=0
    ),

    db: Session = Depends(get_db)
):
    """
    Predict ETA for an actual delivery.

    The Random Forest prediction is saved back to the
    delivery record.

    The predicted arrival is then compared with the
    scheduled arrival.

    If the predicted delay exceeds the configured
    threshold, the delivery is marked as delayed and
    an alert is created.
    """

    # ========================================================
    # FIND DELIVERY
    # ========================================================

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

    # ========================================================
    # DISTANCE
    # ========================================================

    if (
        delivery.distance_remaining_km
        is None
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Delivery does not have "
                "distance_remaining_km. "
                "Start GPS simulation or update "
                "the shipment location first."
            )
        )

    if (
        delivery.distance_remaining_km
        < 0
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Delivery distance cannot "
                "be negative"
            )
        )

    # ========================================================
    # RESTOCK ORDER
    # ========================================================

    restock_order = db.query(
        RestockOrder
    ).filter(
        RestockOrder.id
        == delivery.restock_order_id
    ).first()

    if not restock_order:

        raise HTTPException(
            status_code=404,
            detail=(
                "Restock order linked to "
                "delivery was not found"
            )
        )

    quantity = (
        restock_order.quantity
    )

    if (
        quantity is None
        or quantity <= 0
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Restock order quantity "
                "must be greater than zero"
            )
        )

    # ========================================================
    # RUN RANDOM FOREST ETA MODEL
    # ========================================================

    try:

        prediction = predict_eta(
            distance_km=(
                delivery.distance_remaining_km
            ),

            quantity=quantity,

            supplier_delay_history=(
                supplier_delay_history
            ),

            carrier_delay_history=(
                carrier_delay_history
            )
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc)
        )

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=(
                f"ETA prediction failed: {exc}"
            )
        )

    # ========================================================
    # SAVE ETA TO DELIVERY
    # ========================================================

    delivery.estimated_arrival = (
        prediction[
            "estimated_arrival"
        ]
    )

    delivery.eta_minutes = (
        prediction[
            "estimated_delivery_minutes"
        ]
    )

    # ========================================================
    # CALCULATE PREDICTED DELAY
    # ========================================================

    predicted_delay_minutes = 0.0

    is_delayed = False

    if (
        delivery.scheduled_arrival
        is not None
    ):

        predicted_delay_minutes = max(
            0.0,
            (
                delivery.estimated_arrival
                - delivery.scheduled_arrival
            ).total_seconds()
            / 60
        )

        if (
            predicted_delay_minutes
            > delay_threshold_minutes
        ):

            is_delayed = True

    # ========================================================
    # DELAY PROCESSING
    # ========================================================

    alert_created = False

    if is_delayed:

        delivery.delay_detected = True

        # ----------------------------------------------------
        # Only change travelling states
        # ----------------------------------------------------

        if delivery.status in {
            "scheduled",
            "in_transit"
        }:

            delivery.status = (
                "delayed"
            )

        # ----------------------------------------------------
        # CHECK EXISTING DELAY ALERT
        # ----------------------------------------------------

        existing_alert = db.query(
            Alert
        ).filter(
            Alert.delivery_id
            == delivery.id,

            Alert.alert_type
            == "delay",

            Alert.resolved
            == False
        ).first()

        # ----------------------------------------------------
        # CREATE ALERT
        # ----------------------------------------------------

        if not existing_alert:

            trailer_label = (
                delivery.trailer_id
                or delivery.tracking_number
                or f"delivery {delivery.id}"
            )

            alert = Alert(
                delivery_id=(
                    delivery.id
                ),

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

            db.add(
                alert
            )

            alert_created = True

    # ========================================================
    # SAVE DATABASE CHANGES
    # ========================================================

    db.commit()

    db.refresh(
        delivery
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "delivery_id": (
            delivery.id
        ),

        "tracking_number": (
            delivery.tracking_number
        ),

        "trailer_id": (
            delivery.trailer_id
        ),

        "model": (
            "RandomForestRegressor"
        ),

        "inputs": {
            "distance_km": (
                delivery.distance_remaining_km
            ),

            "quantity": float(
                quantity
            ),

            "supplier_delay_history": (
                supplier_delay_history
            ),

            "carrier_delay_history": (
                carrier_delay_history
            )
        },

        "prediction": {
            "estimated_delivery_hours": (
                prediction[
                    "estimated_delivery_hours"
                ]
            ),

            "estimated_delivery_minutes": (
                prediction[
                    "estimated_delivery_minutes"
                ]
            ),

            "estimated_arrival": (
                delivery.estimated_arrival
            )
        },

        "schedule": {
            "scheduled_arrival": (
                delivery.scheduled_arrival
            ),

            "predicted_delay_minutes": round(
                predicted_delay_minutes,
                2
            ),

            "delay_threshold_minutes": (
                delay_threshold_minutes
            )
        },

        "delay": {
            "delay_detected": (
                is_delayed
            ),

            "alert_created": (
                alert_created
            ),

            "current_status": (
                delivery.status
            )
        },

        "evaluated_at": (
            datetime.utcnow()
        )
    }