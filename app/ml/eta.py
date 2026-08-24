import os
import joblib
from datetime import datetime, timedelta

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "saved_models",
    "eta_model.pkl"
)

model = joblib.load(MODEL_PATH)


def predict_eta(
    distance_km: float,
    quantity: float,
    supplier_delay_history: float,
    carrier_delay_history: float
):
    """
    Predict delivery time in hours.

    distance_km:
        Distance between supplier and destination.

    quantity:
        Quantity of products being delivered.

    supplier_delay_history:
        Historical delay value for the supplier.

    carrier_delay_history:
        Historical delay value for the carrier.
    """

    prediction = model.predict([
        [
            distance_km,
            quantity,
            supplier_delay_history,
            carrier_delay_history
        ]
    ])

    delivery_hours = float(prediction[0])

    eta = datetime.utcnow() + timedelta(hours=delivery_hours)

    return {
        "estimated_delivery_hours": round(delivery_hours, 2),
        "estimated_arrival": eta
    }