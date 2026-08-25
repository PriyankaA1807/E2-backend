# ETA Prediction API

The ETA API provides machine-learning-based shipment arrival prediction for the E2 backend.

The current ETA model is a:

```text
RandomForestRegressor
```

The API supports two prediction modes:

1. direct prediction using manually supplied model features;
2. delivery-aware prediction using an existing E2 Delivery.

**Base path:** `/eta`

---

# Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/eta/predict` | Run direct ML ETA prediction using query parameters |
| POST | `/eta/predict-delivery/{delivery_id}` | Predict ETA for an existing E2 Delivery and evaluate delay |

---

# ETA Architecture

```text
                       ETA API
                          │
             ┌────────────┴────────────┐
             │                         │
             ▼                         ▼
      Direct Prediction         Delivery Prediction
      GET /eta/predict          POST /eta/predict-delivery
             │                         │
             ▼                         ▼
      Query Parameters              Delivery
             │                         │
             ▼                         ├── Distance
      ML Input Features               ├── Quantity
             │                         ├── Schedule
             │                         └── Current State
             └────────────┬────────────┘
                          ▼
                 Random Forest Model
                          │
                          ▼
                 Predicted Duration
                          │
                          ▼
                 Estimated Arrival
                          │
                          ▼
                 Delay Evaluation
                   (delivery mode)
```

---

# 1. Direct ETA Prediction

## Endpoint

```http
GET /eta/predict
```

Runs the trained ETA model using feature values supplied directly through query parameters.

This endpoint does not require an E2 Delivery to exist.

---

# Query Parameters

| Parameter | Type | Required | Description |
|---|---|---:|---|
| `distance_km` | float | Yes | Shipment distance in kilometers |
| `quantity` | float | Yes | Shipment quantity |
| `supplier_delay_history` | float | Yes | Historical supplier-delay input |
| `carrier_delay_history` | float | Yes | Historical carrier-delay input |

---

# Example Request

```http
GET /eta/predict?distance_km=500&quantity=100&supplier_delay_history=2&carrier_delay_history=1
```

No JSON request body is required.

---

# Model Input Features

The trained model expects:

```text
distance_km
quantity
supplier_delay_history
carrier_delay_history
```

Conceptually:

```text
distance_km
      +
quantity
      +
supplier_delay_history
      +
carrier_delay_history
      ↓
RandomForestRegressor
      ↓
Estimated Delivery Hours
      ↓
Current UTC Time
      +
Predicted Hours
      ↓
Estimated Arrival
```

---

# Example Successful Response

```http
200 OK
```

```json
{
  "estimated_delivery_hours": 12.34,
  "estimated_arrival": "2026-08-25T20:34:00"
}
```

---

# Response Fields

| Field | Type | Description |
|---|---|---|
| `estimated_delivery_hours` | float | ML-predicted delivery duration in hours |
| `estimated_arrival` | datetime | Current UTC time plus predicted duration |

The exact values depend on both the model output and the time of prediction.

---

# Direct Prediction Backend Logic

```text
Receive Query Parameters
        ↓
Build Model Features
        ↓
RandomForestRegressor.predict(...)
        ↓
Predicted Delivery Hours
        ↓
Convert Prediction to Float
        ↓
Current UTC + Prediction
        ↓
Return ETA
```

This endpoint behaves primarily as a standalone ML prediction service.

It does not require:

```text
Delivery ID
Tracking Number
Trailer ID
Shipment Reference
```

---

# 2. Delivery-Aware ETA Prediction

## Endpoint

```http
POST /eta/predict-delivery/{delivery_id}
```

Runs the ETA model for an existing E2 Delivery and integrates the prediction into the shipment workflow.

Unlike the basic prediction endpoint, this API can:

```text
Load Delivery
    ↓
Load Related Restock Order
    ↓
Read Quantity
    ↓
Use Remaining Distance
    ↓
Run ML Prediction
    ↓
Update Estimated Arrival
    ↓
Update ETA Minutes
    ↓
Compare Against Scheduled Arrival
    ↓
Detect Predicted Delay
    ↓
Update Delivery
    ↓
Create / Reuse Delay Alert
```

---

# Path Parameter

| Parameter | Type | Required | Description |
|---|---|---:|---|
| `delivery_id` | integer | Yes | Existing E2 Delivery ID |

---

# Query Parameters

| Parameter | Type | Required | Default / Rule | Description |
|---|---|---:|---|---|
| `supplier_delay_history` | float | No | `0` | Historical supplier-delay feature |
| `carrier_delay_history` | float | No | `0` | Historical carrier-delay feature |
| `delay_threshold_minutes` | float | No | `15` | Minimum predicted lateness required before considering the shipment delayed |

These values must be non-negative.

---

# Example Request

```http
POST /eta/predict-delivery/2?supplier_delay_history=0&carrier_delay_history=0&delay_threshold_minutes=15
```

No request body is required.

---

# Delivery Data Used

The endpoint derives model information from the existing Delivery and its related RestockOrder.

Typical mapping:

```text
distance_km
    ↓
Delivery.distance_remaining_km

quantity
    ↓
Delivery
    ↓
RestockOrder.quantity

supplier_delay_history
    ↓
Query Parameter

carrier_delay_history
    ↓
Query Parameter
```

This means callers do not need to manually send the shipment distance and quantity when using the delivery-aware endpoint.

---

# Prediction Flow

```text
delivery_id
    ↓
Find Delivery
    ↓
Delivery exists?
    ├── No → 404
    │
    └── Yes
         ↓
Read distance_remaining_km
         ↓
Read RestockOrder quantity
         ↓
Add supplier/carrier history
         ↓
RandomForestRegressor
         ↓
Estimated Delivery Hours
         ↓
Estimated Delivery Minutes
         ↓
Estimated Arrival
         ↓
Update Delivery
```

---

# Example Successful Response

The following response was produced during E2 testing:

```json
{
  "delivery_id": 2,
  "tracking_number": "TR-2045",
  "trailer_id": null,
  "model": "RandomForestRegressor",
  "inputs": {
    "distance_km": 1461.0756234171756,
    "quantity": 50,
    "supplier_delay_history": 0,
    "carrier_delay_history": 0
  },
  "prediction": {
    "estimated_delivery_hours": 29.47,
    "estimated_delivery_minutes": 1768.39,
    "estimated_arrival": "2026-08-26T19:22:18.668918"
  },
  "schedule": {
    "scheduled_arrival": "2026-08-24T12:00:00",
    "predicted_delay_minutes": 3322.31,
    "delay_threshold_minutes": 15
  },
  "delay": {
    "delay_detected": true,
    "alert_created": false,
    "current_status": "delayed"
  },
  "evaluated_at": "2026-08-25T13:53:55.345773"
}
```

---

# Response Structure

## Top-Level Fields

| Field | Type | Description |
|---|---|---|
| `delivery_id` | integer | E2 Delivery being evaluated |
| `tracking_number` | string / null | Shipment tracking number |
| `trailer_id` | string / null | Trailer identifier |
| `model` | string | ML model used |
| `inputs` | object | Model features used |
| `prediction` | object | ETA prediction |
| `schedule` | object | Schedule-vs-prediction comparison |
| `delay` | object | Delay evaluation result |
| `evaluated_at` | datetime | Prediction evaluation time |

---

# Inputs Object

Example:

```json
{
  "distance_km": 1461.0756234171756,
  "quantity": 50,
  "supplier_delay_history": 0,
  "carrier_delay_history": 0
}
```

| Field | Type | Description |
|---|---|---|
| `distance_km` | float | Remaining delivery distance |
| `quantity` | float | Shipment/restock quantity |
| `supplier_delay_history` | float | Supplier historical delay input |
| `carrier_delay_history` | float | Carrier historical delay input |

---

# Prediction Object

Example:

```json
{
  "estimated_delivery_hours": 29.47,
  "estimated_delivery_minutes": 1768.39,
  "estimated_arrival": "2026-08-26T19:22:18.668918"
}
```

| Field | Type | Description |
|---|---|---|
| `estimated_delivery_hours` | float | ML-predicted duration |
| `estimated_delivery_minutes` | float | Prediction converted to minutes |
| `estimated_arrival` | datetime | Predicted arrival timestamp |

---

# Schedule Object

Example:

```json
{
  "scheduled_arrival": "2026-08-24T12:00:00",
  "predicted_delay_minutes": 3322.31,
  "delay_threshold_minutes": 15
}
```

| Field | Type | Description |
|---|---|---|
| `scheduled_arrival` | datetime / null | Planned arrival |
| `predicted_delay_minutes` | float | Difference between predicted and scheduled arrival |
| `delay_threshold_minutes` | float | Configured threshold before delay is considered significant |

---

# Delay Object

Example:

```json
{
  "delay_detected": true,
  "alert_created": false,
  "current_status": "delayed"
}
```

| Field | Type | Description |
|---|---|---|
| `delay_detected` | boolean | Whether predicted lateness crossed the threshold |
| `alert_created` | boolean | Whether a new alert was created during this request |
| `current_status` | string | Current Delivery status after evaluation |

---

# Why `alert_created` Can Be False During a Delay

A response can contain:

```json
{
  "delay_detected": true,
  "alert_created": false
}
```

This does not mean alert handling failed.

It can mean an unresolved delay alert already exists.

Conceptually:

```text
Delay detected
      ↓
Check existing unresolved delay alert
      ↓
Alert exists?
   ┌──────┴──────┐
  Yes            No
   ↓              ↓
Reuse state    Create Alert
   ↓              ↓
false           true
```

This avoids generating repeated duplicate alerts whenever ETA is recalculated.

---

# Automatic Delivery Updates

The delivery-aware ETA endpoint is not read-only.

It can update fields on the Delivery.

Conceptually:

```text
ML Prediction
      ↓
Delivery.estimated_arrival
      ↓
Delivery.eta_minutes
```

If a delay is detected:

```text
Delivery.delay_detected = true
```

and the current operational state can become:

```text
delayed
```

depending on shipment state and implementation logic.

---

# Delay Evaluation

Delay is based on the comparison between:

```text
Predicted Arrival
      -
Scheduled Arrival
```

This produces:

```text
predicted_delay_minutes
```

The result is compared with:

```text
delay_threshold_minutes
```

Conceptually:

```text
Predicted Delay = 40 minutes
Threshold       = 15 minutes

40 > 15
   ↓
Delay Detected
```

If the predicted delay does not exceed the threshold, the endpoint does not mark it as a predicted delay.

---

# Alert Integration

When a predicted delay is detected, E2 can create a delay alert if no suitable unresolved delay alert already exists.

The alert can later be retrieved through:

```http
GET /operations/alerts
```

This connects ETA prediction with the Operations layer.

```text
ML ETA
   ↓
Predicted Delay
   ↓
Delivery.delay_detected
   ↓
Operational Alert
   ↓
Dashboard / Frontend
```

---

# Relationship with Operations API

ETA and Operations work together but provide different responsibilities.

## ETA API

Predicts future arrival.

```text
Where will this shipment arrive,
and when?
```

## Operations API

Evaluates operational conditions.

```text
Is this shipment delayed,
exceptional,
or operationally problematic?
```

For example:

```http
POST /operations/detect-delays
```

can evaluate deliveries independently of an explicit ML prediction request.

---

# Relationship with Tracking

Tracking provides current shipment information such as:

```text
Current Latitude
Current Longitude
Current Location
Distance Remaining
Last GPS Update
```

ETA can use the resulting distance information.

Conceptually:

```text
Tracking / GPS
      ↓
Current Position
      ↓
Distance Remaining
      ↓
ML ETA
      ↓
Estimated Arrival
```

---

# Relationship with Restock Orders

The delivery-aware endpoint uses the Delivery's associated RestockOrder to obtain shipment quantity.

```text
Delivery
   │
   ▼
RestockOrder
   │
   ▼
quantity
   │
   ▼
ML Feature
```

The caller therefore does not need to manually know the quantity stored inside E2.

---

# Relationship with PR2 Integration

PR2 can create a shipment using:

```http
POST /integrations/shipments
```

This creates an E2:

```text
RestockOrder
+
Delivery
```

The resulting Delivery can later use:

```http
POST /eta/predict-delivery/{delivery_id}
```

Therefore the cross-service workflow can be:

```text
PR2
 ↓
POST /integrations/shipments
 ↓
E2 Delivery Created
 ↓
Tracking / GPS
 ↓
Remaining Distance
 ↓
POST /eta/predict-delivery/{delivery_id}
 ↓
ML ETA
 ↓
Delay Evaluation
 ↓
Alert / Dashboard
```

---

# ML Model

The ETA model is stored at:

```text
app/ml/saved_models/eta_model.pkl
```

and loaded using:

```text
joblib
```

The trained estimator is:

```text
sklearn.ensemble.RandomForestRegressor
```

The model accepts four features:

```text
distance_km
quantity
supplier_delay_history
carrier_delay_history
```

---

# Why Random Forest?

The ETA problem uses structured/tabular shipment data.

Random Forest is appropriate because it:

- models nonlinear relationships;
- handles interactions between shipment features;
- works well with structured data;
- does not require neural-network-level infrastructure;
- is straightforward to serialize;
- can be integrated directly into the Python backend.

---

# Why the Model Is Exposed Through an API

Other applications do not need:

```text
Python
Scikit-learn
Joblib
eta_model.pkl
Training scripts
```

They only need the HTTP API.

For example:

```text
Java Backend
      ↓
HTTP
      ↓
FastAPI
      ↓
Random Forest
      ↓
JSON ETA Response
```

The same applies to:

```text
React
Node.js
Go
.NET
Mobile Apps
Other Services
```

---

# ML ETA vs Simulation ETA

E2 currently has two ETA mechanisms.

## ML ETA

Uses:

```text
Distance
Quantity
Supplier Delay History
Carrier Delay History
        ↓
Random Forest
```

Available through:

```http
GET /eta/predict
```

and:

```http
POST /eta/predict-delivery/{delivery_id}
```

---

## Simulation ETA

GPS simulation can estimate remaining travel time using movement information such as:

```text
Remaining Distance
       ÷
Current / Simulated Speed
       ↓
Remaining Travel Time
```

Simulation endpoints include:

```http
POST /simulation/start/{delivery_id}
POST /simulation/step/{delivery_id}
POST /simulation/stop/{delivery_id}
```

These mechanisms are related but not identical.

```text
ML ETA
≠
Simulation ETA Formula
```

The Random Forest model is not necessarily executed for every GPS movement.

---

# Frontend Integration

For an existing E2 shipment, the recommended frontend/backend flow is:

```text
Delivery
   ↓
Current Tracking State
   ↓
POST /eta/predict-delivery/{delivery_id}
   ↓
Receive
   ├── ETA
   ├── Predicted Arrival
   ├── Delay Minutes
   ├── Delay Flag
   └── Alert Status
   ↓
Render Shipment Detail / Dashboard
```

The frontend should not reproduce the Random Forest calculation.

---

# Cross-Team Integration

Another backend can invoke the delivery-aware prediction using only:

```text
delivery_id
supplier_delay_history
carrier_delay_history
delay_threshold_minutes
```

Example:

```http
POST /eta/predict-delivery/4?supplier_delay_history=1&carrier_delay_history=2&delay_threshold_minutes=15
```

The backend handles:

```text
Database Retrieval
Feature Preparation
ML Prediction
Delivery Update
Delay Evaluation
Alert Handling
```

---

# Error Handling

Integrating applications should handle:

| HTTP Status | Meaning |
|---:|---|
| `200` | Prediction completed |
| `404` | Delivery or required linked resource not found |
| `400` | Required shipment state/data is not suitable for prediction |
| `422` | Invalid path/query parameter |
| `500` | Unexpected ML/model/backend processing failure |

FastAPI validation errors use the standard structure:

```json
{
  "detail": [
    {
      "loc": [
        "query",
        "supplier_delay_history"
      ],
      "msg": "Input should be greater than or equal to 0",
      "type": "greater_than_equal"
    }
  ]
}
```

---

# Prediction Requirements

For delivery-aware prediction, E2 requires enough shipment information to derive the model features.

Important data includes:

```text
Delivery exists
Restock Order exists
Quantity available
Distance remaining available
```

If GPS/distance data has not been established yet, the delivery may not be ready for delivery-aware ETA prediction.

---

# Example End-to-End ETA Flow

```text
Shipment Created
      ↓
Status → in_transit
      ↓
GPS Update
      ↓
distance_remaining_km available
      ↓
POST /eta/predict-delivery/{delivery_id}
      ↓
Random Forest Prediction
      ↓
estimated_arrival updated
      ↓
eta_minutes updated
      ↓
Compare with scheduled_arrival
      ↓
Delay?
   ┌──────┴──────┐
   No            Yes
                 ↓
          delay_detected = true
                 ↓
             Alert
                 ↓
            Dashboard
```

---

# Recommended API Usage

## Standalone Model Testing

Use:

```http
GET /eta/predict
```

when you already have all four model features and only need a prediction.

---

## Real E2 Shipment

Use:

```http
POST /eta/predict-delivery/{delivery_id}
```

when the shipment already exists inside E2 and you want ETA prediction integrated with:

```text
Delivery
Restock Order
Delay Detection
Alerts
Dashboard
```

---

# Current Limitations

The current ETA implementation:

- uses four trained features;
- does not automatically retrieve real historical supplier/carrier metrics from an external analytics system;
- does not currently use live traffic APIs;
- does not retrain automatically;
- does not provide model-confidence intervals;
- does not version predictions;
- uses project/training data rather than a production-scale logistics dataset;
- keeps ML prediction and simulation travel-time logic as separate mechanisms.

These limitations do not prevent the current ETA workflow from being used for project integration and demonstration.

---

# Summary

The ETA API supports both standalone ML prediction and delivery-integrated operational prediction.

```text
                ETA
                 │
        ┌────────┴────────┐
        │                 │
Direct Model        Existing Delivery
Prediction          Prediction
        │                 │
        └────────┬────────┘
                 ↓
       RandomForestRegressor
                 ↓
          Estimated Arrival
                 ↓
         Delay Evaluation
                 ↓
      Operations / Dashboard
```

Use:

```http
GET /eta/predict
```

for direct feature-based prediction.

Use:

```http
POST /eta/predict-delivery/{delivery_id}
```

for the complete E2 shipment ETA workflow.
