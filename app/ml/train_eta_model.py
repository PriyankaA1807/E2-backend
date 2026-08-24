import os
import joblib
import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score


np.random.seed(42)


n_samples = 2000

distance_km = np.random.uniform(10, 2000, n_samples)
quantity = np.random.uniform(10, 500, n_samples)
supplier_delay_history = np.random.uniform(0, 8, n_samples)
carrier_delay_history = np.random.uniform(0, 8, n_samples)

# Assume average road speed around 55 km/h.
base_travel_time = distance_km / 55

# Quantity adds a relatively small handling/loading effect.
quantity_effect = quantity * 0.003

# Historical supplier/carrier delays influence ETA.
supplier_effect = supplier_delay_history * 0.6
carrier_effect = carrier_delay_history * 0.7

# Small random operational variation
noise = np.random.normal(0, 0.8, n_samples)

delivery_time_hours = (
    base_travel_time
    + quantity_effect
    + supplier_effect
    + carrier_effect
    + noise
)

# Prevent impossible negative delivery times
delivery_time_hours = np.maximum(delivery_time_hours, 0.5)


df = pd.DataFrame({
    "distance_km": distance_km,
    "quantity": quantity,
    "supplier_delay_history": supplier_delay_history,
    "carrier_delay_history": carrier_delay_history,
    "delivery_time_hours": delivery_time_hours
})


X = df[
    [
        "distance_km",
        "quantity",
        "supplier_delay_history",
        "carrier_delay_history"
    ]
]

y = df["delivery_time_hours"]


X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)


model = RandomForestRegressor(
    n_estimators=200,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)


predictions = model.predict(X_test)

print(f"R² score: {r2_score(y_test, predictions):.3f}")
print(
    f"Mean Absolute Error: "
    f"{mean_absolute_error(y_test, predictions):.2f} hours"
)


model_dir = os.path.join(
    os.path.dirname(__file__),
    "saved_models"
)

os.makedirs(model_dir, exist_ok=True)

model_path = os.path.join(
    model_dir,
    "eta_model.pkl"
)

joblib.dump(model, model_path)

print(f"ETA model saved to: {model_path}")