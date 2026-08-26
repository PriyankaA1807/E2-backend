# ETA API

API documentation for the **ETA Prediction** module of the E2 Smart Restock & Yard Dock Delivery Tracker.

This module predicts shipment arrival time using a trained **RandomForestRegressor** and supports delay detection for active deliveries.

---

## Base URL

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

> Replace the local URL with the deployed backend URL after deployment.

---

# Overview

The ETA module estimates how long an active shipment may take to reach its destination.

The system uses a trained:

```text
RandomForestRegressor
```

The model is loaded from:

```text
app/ml/saved_models/eta_model.pkl
```

The ETA model can be tested independently or used for a real delivery.

---

# Model Inputs

The model uses four input features:

```text
distance_km
quantity
supplier_delay_history
carrier_delay_history
```

---

# Hackathon Input Usage

For the hackathon prototype, these inputs are used as follows.

## distance_km

This value is calculated dynamically from the truck's current simulated GPS location to the destination.

As the truck moves:

```text
GPS changes
    ↓
remaining distance changes
    ↓
distance_km changes
```

This is the primary live-changing input during the simulated journey.

---

## quantity

The shipment quantity comes from the linked restock order.

Example:

```text
Delivery
   ↓
Restock Order
   ↓
quantity
```

---

## supplier_delay_history

For the hackathon automatic simulation, this currently uses a prototype/default value.

Example:

```text
0.0
```

In a production system, this could come from historical supplier performance data.

---

## carrier_delay_history

For the hackathon automatic simulation, this also uses a prototype/default value.

Example:

```text
0.0
```

In a production system, this could come from historical carrier performance data.

---

# Important Hackathon Note

The project does **not** require a full historical supplier or carrier analytics platform.

The two history inputs are included to demonstrate that the ML model can consider historical logistics reliability.

For the hackathon:

```text
distance_km → dynamic simulated delivery data
quantity → linked restock order
supplier_delay_history → prototype/default value
carrier_delay_history → prototype/default value
```

This is enough for the prototype.

---

# 1. Standalone ETA Prediction

## Endpoint

```http
GET /eta/predict
```

This endpoint allows direct testing of the trained Random Forest ETA model without requiring an existing delivery.

---

## Query Parameters

| Parameter                | Type  | Required | Description                               |
| ------------------------ | ----- | -------- | ----------------------------------------- |
| `distance_km`            | float | Yes      | Remaining delivery distance in kilometers |
| `quantity`               | float | Yes      | Shipment quantity                         |
| `supplier_delay_history` | float | Yes      | Supplier historical delay input           |
| `carrier_delay_history`  | float | Yes      | Carrier historical delay input            |

---

## Example Request

```http
GET /eta/predict?distance_km=500&quantity=100&supplier_delay_history=2&carrier_delay_history=1
```

---

## Example Response

```json
{
  "estimated_delivery_hours": 11.28,
  "estimated_delivery_minutes": 676.8,
  "estimated_arrival": "2026-08-26T20:00:00"
}
```

The exact prediction depends on the trained model.

---

# 2. Delivery-Aware ETA Prediction

## Endpoint

```http
POST /eta/predict-delivery/{delivery_id}
```

Predicts ETA for an existing delivery.

The endpoint uses information already stored for the delivery and its linked restock order.

---

## Path Parameter

| Parameter     | Type    | Required | Description                            |
| ------------- | ------- | -------- | -------------------------------------- |
| `delivery_id` | integer | Yes      | Delivery whose ETA should be predicted |

---

## Optional Query Parameters

| Parameter                 | Type  | Default | Description                          |
| ------------------------- | ----- | ------: | ------------------------------------ |
| `supplier_delay_history`  | float |   `0.0` | Supplier delay-history input         |
| `carrier_delay_history`   | float |   `0.0` | Carrier delay-history input          |
| `delay_threshold_minutes` | float |  `15.0` | Delay threshold used for alert logic |

---

## Example Request

```http
POST /eta/predict-delivery/3?supplier_delay_history=0&carrier_delay_history=0&delay_threshold_minutes=15
```

---

# Internal Flow

The endpoint follows this process:

```text
Find Delivery
     ↓
Read distance_remaining_km
     ↓
Find linked Restock Order
     ↓
Read quantity
     ↓
Run Random Forest model
     ↓
Get predicted ETA
     ↓
Save ETA to Delivery
     ↓
Compare with scheduled arrival
     ↓
Detect delay if required
     ↓
Create delay alert if required
```

---

# Distance Requirement

The delivery must already have a valid:

```text
distance_remaining_km
```

If distance is missing, the ETA endpoint cannot perform a delivery prediction.

This usually means the shipment should first have:

* GPS data
* a simulated location update
* or an active simulation

---

## Example Error

```json
{
  "detail": "Delivery does not have distance_remaining_km. Start GPS simulation or update the shipment location first."
}
```

---

# Random Forest Prediction

The model receives:

```text
distance_km
quantity
supplier_delay_history
carrier_delay_history
```

and predicts a delivery duration.

The prediction is converted into:

```text
estimated_delivery_hours
estimated_delivery_minutes
estimated_arrival
```

---

# Saving ETA to Delivery

The result is stored in the delivery record.

The backend updates:

```text
delivery.eta_minutes
delivery.estimated_arrival
```

This allows the tracking API and frontend dashboard to display the current ETA.

---

# Delay Detection

After predicting the arrival time, the system compares:

```text
estimated_arrival
```

with:

```text
scheduled_arrival
```

The backend calculates:

```text
predicted_delay_minutes
```

If:

```text
predicted_delay_minutes > delay_threshold_minutes
```

then the delivery can be marked as delayed.

Example:

```text
Scheduled Arrival = 3:00 PM
Predicted Arrival = 3:40 PM
Threshold = 15 minutes

Predicted Delay = 40 minutes

40 > 15
    ↓
Delay detected
```

---

# Delay Processing

When a delay is detected:

```text
delay_detected = true
```

For travelling states such as:

```text
scheduled
in_transit
```

the delivery status can become:

```text
delayed
```

---

# Delay Alert

If no unresolved delay alert already exists, the backend creates an operational alert.

Example alert:

```json
{
  "alert_type": "delay",
  "severity": "high",
  "title": "Predicted Shipment Delay",
  "message": "Trailer TRL-101 is predicted to arrive 40.0 minutes late."
}
```

The alert can then be viewed from:

```http
GET /operations/alerts
```

For the hackathon, these alerts are shown to the single **Operations Admin** view.

---

# Example Delivery ETA Response

```json
{
  "delivery_id": 3,
  "tracking_number": "TRK-E2-101",
  "trailer_id": "TRL-101",
  "model": "RandomForestRegressor",
  "inputs": {
    "distance_km": 102.99,
    "quantity": 100,
    "supplier_delay_history": 0,
    "carrier_delay_history": 0
  },
  "prediction": {
    "estimated_delivery_hours": 4.27,
    "estimated_delivery_minutes": 256.33,
    "estimated_arrival": "2026-08-26T09:07:14"
  },
  "schedule": {
    "scheduled_arrival": "2026-08-25T15:00:00",
    "predicted_delay_minutes": 0,
    "delay_threshold_minutes": 15
  },
  "delay": {
    "delay_detected": true,
    "alert_created": true,
    "current_status": "delayed"
  },
  "evaluated_at": "2026-08-26T04:50:54"
}
```

Values above are illustrative and depend on the current delivery state and model output.

---

# Dynamic ETA During Automatic Simulation

The ETA is also used during the automatic background truck simulation.

The full flow is:

```text
Truck moves
    ↓
New GPS coordinates
    ↓
Remaining distance recalculated
    ↓
Random Forest receives updated distance
    ↓
New ETA predicted
    ↓
Delivery ETA updated
    ↓
Delay checked
```

So the frontend can observe ETA changing while the truck marker moves.

---

# Arrival Behavior

When the truck reaches the yard gate:

```text
status = arrived_at_gate
distance_remaining_km = 0
eta_minutes = 0
simulation_active = false
```

At this point, no delivery time remains because the truck has reached its destination.

---

# Difference Between Start ETA and Live ETA

When simulation begins, the start endpoint may provide an initial ETA estimate.

After background tracking begins, the live delivery ETA is recalculated using the Random Forest ETA pipeline.

For the frontend, the latest tracking state should be treated as the current source of truth.

---

# Model Purpose

The model is used to demonstrate ML-based ETA prediction for the hackathon.

It is not presented as a production-grade logistics model.

The main goal is to show the pipeline:

```text
Shipment Data
    ↓
ML ETA Model
    ↓
Predicted Arrival
    ↓
Delay Detection
    ↓
Operational Alert
```

---

# Why Random Forest?

Random Forest is suitable for this prototype because it:

* Works well with tabular numerical data
* Can model nonlinear relationships
* Requires limited preprocessing
* Is simple to integrate with Python/FastAPI
* Can use multiple operational factors together

---

# Production Extension

In a production system, additional features could be included, such as:

```text
traffic conditions
weather
route congestion
driver behavior
vehicle type
historical route duration
warehouse congestion
day of week
time of day
carrier reliability
supplier reliability
```

The current hackathon model intentionally stays lightweight.

---

# Frontend Usage

For the frontend, the main ETA values are normally obtained through the tracking/delivery state.

Useful fields include:

```text
eta_minutes
estimated_arrival
distance_remaining_km
delay_detected
status
```

The frontend can update these values every few seconds while polling the tracking endpoint.

---

# Recommended Demo Flow

For the ETA demonstration:

```text
1. Start truck simulation
2. Show initial distance
3. Show initial ETA
4. Wait for automatic truck movement
5. Fetch tracking state again
6. Show decreased distance
7. Show recalculated ETA
8. Show delay_detected if applicable
9. Show Operations Admin alert
10. Let truck reach Yard Gate
11. Show ETA = 0
```

---

# Summary

The ETA API provides:

* Standalone Random Forest ETA prediction
* Delivery-aware ETA prediction
* Dynamic ETA updates
* Delay calculation
* Delay threshold handling
* Automatic delay alerts
* Integration with simulated real-time truck movement

For the hackathon, the model uses real delivery/simulation values where available and prototype/default historical-delay values where enterprise historical data is unavailable.
