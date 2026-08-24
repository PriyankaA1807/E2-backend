import os
import joblib


MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    "saved_models",
    "eta_model.pkl"
)


model = joblib.load(MODEL_PATH)


def predict_eta(
    distance_km: float,
    quantity: int,
    supplier_delay_history: float,
    carrier_delay_history: float
):

    prediction = model.predict([
        [
            distance_km,
            quantity,
            supplier_delay_history,
            carrier_delay_history
        ]
    ])

    return round(float(prediction[0]), 2)