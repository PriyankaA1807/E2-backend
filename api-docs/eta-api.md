# ETA Prediction API

The ETA API predicts the estimated delivery time of a shipment using the trained machine-learning model included in the E2 backend.

The current ETA model is a **Random Forest Regressor**.

**Base path:** `/eta`

---

## Endpoint

| Method | Endpoint       | Purpose                         |
| ------ | -------------- | ------------------------------- |
| GET    | `/eta/predict` | Predict estimated delivery time |

---

# Predict ETA

## `GET /eta/predict`

Calculates an estimated delivery duration using shipment and historical delay information.

Unlike APIs that accept JSON bodies, this endpoint receives its model inputs through **query parameters**.

---

# Query Parameters

| Parameter                | Type    | Required | Description                     |
| ------------------------ | ------- | -------: | ------------------------------- |
| `distance_km`            | float   |      Yes | Shipment distance in kilometers |
| `quantity`               | integer |      Yes | Quantity being transported      |
| `supplier_delay_history` | float   |      Yes | Historical supplier delay input |
| `carrier_delay_history`  | float   |      Yes | Historical carrier delay input  |

---

# Example Request

```http
GET /eta/predict?distance_km=500&quantity=100&supplier_delay_history=2&carrier_delay_history=1
```

No request body is required.

---

# Prediction Flow

The API passes the four input features to the saved ETA model.

```text
distance_km
      │
quantity
      │
supplier_delay_history
      │
carrier_delay_history
      │
      ▼
Random Forest Regressor
      │
      ▼
Predicted Delivery Hours
      │
      ▼
Current UTC Time
      +
Predicted Hours
      │
      ▼
Estimated Arrival
```

---

# ML Input Features

The saved model expects these features:

```text
distance_km
quantity
supplier_delay_history
carrier_delay_history
```

The API constructs the prediction input using those feature names before sending it to the model.

This is important for another service integrating with the model: the current endpoint does **not** accept arbitrary ML features.

---

# Successful Response

The API returns:

```json
{
  "estimated_delivery_hours": 12.34,
  "estimated_arrival": "2026-08-25T08:34:00"
}
```

| Field                      | Type     | Description                                      |
| -------------------------- | -------- | ------------------------------------------------ |
| `estimated_delivery_hours` | float    | Predicted number of hours required for delivery  |
| `estimated_arrival`        | datetime | Estimated arrival calculated from the prediction |

The exact values depend on the model prediction and the time at which the request is made.

---

# Backend Logic

Conceptually:

```text
Receive query parameters
        ↓
Create model input
        ↓
Load/use saved ETA model
        ↓
model.predict(...)
        ↓
Receive predicted hours
        ↓
Convert prediction to float
        ↓
Current UTC time + predicted hours
        ↓
Return prediction + arrival time
```

The endpoint performs prediction only. It does not create a Delivery, TrackingEvent, RestockOrder, or Alert.

---

# Machine Learning Model

The model stored in the backend is a:

```text
RandomForestRegressor
```

from scikit-learn.

The trained model is stored under the backend's ML saved-model directory and is loaded for ETA prediction.

The API layer allows other applications to use the prediction without needing to understand or directly run the Python ML code.

For example:

```text
React / Mobile / Java / Node Service
                ↓
        GET /eta/predict
                ↓
          FastAPI Backend
                ↓
        Random Forest Model
                ↓
          ETA Prediction
                ↓
        JSON HTTP Response
```

---

# Why the ML Model Is Behind an API

An integrating service does not need:

* Python
* scikit-learn
* the `.pkl` model file
* the model training script
* knowledge of Random Forest implementation details

It only needs to send the four required inputs through HTTP and consume the returned prediction.

This keeps the ML implementation inside E2 while exposing a language-independent integration contract.

---

# Important: ML ETA vs Simulation ETA

The project currently has **two different ETA calculations**.

## 1. ML ETA

Provided by:

```http
GET /eta/predict
```

Uses:

```text
Distance
Quantity
Supplier Delay History
Carrier Delay History
        ↓
Random Forest
        ↓
Predicted Delivery Hours
```

---

## 2. GPS Simulation ETA

During shipment simulation, ETA is calculated from the shipment's current movement information.

Conceptually:

```text
Remaining Distance
       ÷
Current / Simulated Speed
       ↓
Remaining Travel Time
       ↓
Simulation ETA
```

The GPS simulation does **not currently call the Random Forest model on every movement update**.

Therefore:

```text
ML ETA ≠ Simulation ETA mechanism
```

They should be treated as separate calculations in the current implementation.

---

# Frontend Integration

A frontend can request an ML-based ETA when the required prediction inputs are available.

Example:

```text
Shipment Data
     ↓
distance_km = 500
quantity = 100
supplier_delay_history = 2
carrier_delay_history = 1
     ↓
GET /eta/predict
     ↓
{
  estimated_delivery_hours,
  estimated_arrival
}
     ↓
Display ETA
```

Example UI:

```text
Predicted Delivery Time: 12.34 hours

Estimated Arrival:
25 Aug 2026, 08:34
```

The frontend should display the values returned by the backend rather than reproducing the Random Forest calculation itself.

---

# Cross-Team Integration

Any other backend can consume the prediction in the same way.

For example:

```text
Other Backend
     ↓
HTTP GET /eta/predict
     ↓
E2 ML Service
     ↓
Random Forest Prediction
     ↓
JSON Response
```

This means another team can integrate the ETA feature regardless of whether their application uses Java, JavaScript, Go, .NET, or another technology.

---

# Relationship with Delivery

The ETA prediction endpoint itself does not require a `delivery_id`.

Instead, it accepts the four model features directly.

Therefore:

```text
Delivery / External Data
        ↓
Extract required model inputs
        ↓
GET /eta/predict
        ↓
Prediction
```

The caller is responsible for supplying the required feature values.

---

# Error Handling

The integrating application should handle:

| HTTP Status | Meaning                                                                   |
| ----------: | ------------------------------------------------------------------------- |
|       `200` | Prediction completed successfully                                         |
|       `422` | Required query parameter is missing or has an invalid type                |
|       `500` | Prediction/model processing failure if an unexpected backend error occurs |

For example, calling the endpoint without a required parameter can produce FastAPI validation error `422`.

---

# Current Limitations

The current ETA API:

* Accepts only the four trained model features
* Does not accept a `delivery_id` directly for ML prediction
* Does not automatically fetch Supplier or Carrier history from the database
* Does not automatically update a Delivery with the returned ML prediction
* Is separate from the GPS simulation ETA calculation

The endpoint should therefore be treated as a **prediction service**:

```text
Inputs
   ↓
ML Model
   ↓
Prediction
   ↓
Response
```

rather than as a complete shipment-update workflow.
