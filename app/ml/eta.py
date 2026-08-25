import os
from datetime import datetime, timedelta

import joblib
import pandas as pd


# ============================================================
# MODEL PATH
# ============================================================

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "saved_models",
    "eta_model.pkl"
)


# ============================================================
# LOAD MODEL ONCE
# ============================================================

model = joblib.load(MODEL_PATH)


# ============================================================
# MODEL FEATURE ORDER
# ============================================================

MODEL_FEATURES = [
    "distance_km",
    "quantity",
    "supplier_delay_history",
    "carrier_delay_history"
]


# ============================================================
# ETA PREDICTION
# ============================================================

def predict_eta(
    distance_km: float,
    quantity: float,
    supplier_delay_history: float,
    carrier_delay_history: float
):
    """
    Predict delivery duration using the trained
    RandomForestRegressor.

    Returns:
    - estimated delivery hours
    - estimated delivery minutes
    - estimated arrival timestamp
    """

    # --------------------------------------------------------
    # Validate inputs
    # --------------------------------------------------------

    if distance_km < 0:
        raise ValueError(
            "distance_km cannot be negative"
        )

    if quantity <= 0:
        raise ValueError(
            "quantity must be greater than zero"
        )

    # --------------------------------------------------------
    # Build dataframe using the exact model feature names
    # --------------------------------------------------------

    features = pd.DataFrame(
        [
            {
                "distance_km": distance_km,
                "quantity": quantity,
                "supplier_delay_history":
                    supplier_delay_history,
                "carrier_delay_history":
                    carrier_delay_history
            }
        ],
        columns=MODEL_FEATURES
    )

    # --------------------------------------------------------
    # Predict
    # --------------------------------------------------------

    prediction = model.predict(
        features
    )

    delivery_hours = max(
        0.0,
        float(prediction[0])
    )

    delivery_minutes = (
        delivery_hours * 60
    )

    estimated_arrival = (
        datetime.utcnow()
        + timedelta(
            hours=delivery_hours
        )
    )

    return {
        "estimated_delivery_hours": round(
            delivery_hours,
            2
        ),

        "estimated_delivery_minutes": round(
            delivery_minutes,
            2
        ),

        "estimated_arrival": (
            estimated_arrival
        )
    }