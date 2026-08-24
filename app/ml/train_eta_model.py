import os
import joblib
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split


# Sample historical delivery data
# In the real project, this will come from the database.
data = {
    "distance_km": [
        10, 25, 40, 15, 60,
        30, 45, 20, 70, 35,
        50, 18, 80, 55, 12,
        42, 65, 28, 75, 22
    ],

    "quantity": [
        20, 50, 100, 30, 150,
        80, 120, 40, 200, 70,
        110, 25, 180, 130, 15,
        90, 160, 60, 190, 45
    ],

    "supplier_delay_history": [
        0.5, 1.2, 2.0, 0.8, 3.0,
        1.5, 2.2, 0.6, 3.5, 1.0,
        2.5, 0.4, 4.0, 2.8, 0.3,
        1.8, 3.2, 1.1, 3.8, 0.7
    ],

    "carrier_delay_history": [
        0.3, 1.0, 1.8, 0.5, 2.5,
        1.2, 2.0, 0.4, 3.0, 0.8,
        2.1, 0.3, 3.5, 2.2, 0.2,
        1.5, 2.8, 0.9, 3.2, 0.6
    ],

    # Target: actual delivery time in hours
    "delivery_time_hours": [
        1.2, 2.8, 4.5, 1.8, 7.2,
        3.6, 5.4, 2.0, 8.5, 3.1,
        6.0, 1.5, 9.2, 6.8, 1.0,
        4.8, 7.5, 2.9, 8.8, 2.5
    ]
}


df = pd.DataFrame(data)


# Features
X = df[
    [
        "distance_km",
        "quantity",
        "supplier_delay_history",
        "carrier_delay_history"
    ]
]

# Target
y = df["delivery_time_hours"]


# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)


# Create ML model
model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)


# Train
model.fit(X_train, y_train)


# Check model score
score = model.score(X_test, y_test)

print(f"Model R² score: {score:.2f}")


# Create model directory
model_dir = os.path.join(
    os.path.dirname(__file__),
    "saved_models"
)

os.makedirs(model_dir, exist_ok=True)


# Save model
model_path = os.path.join(
    model_dir,
    "eta_model.pkl"
)

joblib.dump(model, model_path)

print(f"ETA model saved to: {model_path}")