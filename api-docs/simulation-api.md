**# Simulation API

API documentation for the **GPS & Simulation** module of the E2 Smart Restock & Yard Dock Delivery Tracker.

This module provides simulated real-time truck movement, simulation control, and the simulated WMS feed used by the frontend and operations dashboard.

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

The simulation module is used to simulate inbound truck movement toward the warehouse or yard.

The truck is not connected to a physical GPS device.

Instead, the backend automatically changes the truck's latitude and longitude over time to simulate a real GPS feed.

The normal frontend flow is:

```text
Start Simulation Once
        ↓
Backend Background Tracking
        ↓
Truck Coordinates Change Automatically
        ↓
Distance Recalculated
        ↓
ETA Recalculated
        ↓
Frontend Polls Tracking API
        ↓
Map Marker Moves
```

---

# 1. Start GPS Simulation

## Endpoint

```http
POST /simulation/start/{delivery_id}
```

Starts simulated GPS tracking for a delivery.

The endpoint only needs to be called once to start the journey.

After it is started, the backend background tracking process automatically moves the truck.

---

## Path Parameter

| Parameter     | Type    | Required | Description                                |
| ------------- | ------- | -------- | ------------------------------------------ |
| `delivery_id` | integer | Yes      | Delivery whose GPS simulation should start |

---

## Example Request

```http
POST /simulation/start/3
```

---

## Example Response

```json
{
  "message": "Simulation started",
  "delivery_id": 3,
  "tracking_number": "TRK-E2-101",
  "trailer_id": "TRL-101",
  "status": "in_transit",
  "simulation_active": true,
  "current_latitude": 27.10505,
  "current_longitude": 78.09552,
  "current_location": "27.10505, 78.09552",
  "distance_remaining_km": 717.92,
  "eta_minutes": 861.51,
  "estimated_arrival": "2026-08-26T19:11:48"
}
```

---

## What Happens Internally

When the simulation starts:

```text
Find Delivery
        ↓
Check Destination Coordinates
        ↓
Create Simulated Starting Position if Required
        ↓
status = in_transit
        ↓
simulation_active = true
        ↓
Calculate Initial Distance
        ↓
Calculate Initial ETA
        ↓
Create Tracking Event
        ↓
Background Tracking Continues Automatically
```

If the delivery was already used in an earlier simulation and had reached the yard, the simulator can generate a fresh starting location for another hackathon demonstration.

---

# 2. Automatic Background Truck Movement

After:

```http
POST /simulation/start/{delivery_id}
```

the frontend does not need to manually move the truck.

The backend automatically processes deliveries where:

```text
simulation_active = true
```

The automatic background flow is:

```text
Current GPS Position
        ↓
Move Toward Destination
        ↓
New Latitude / Longitude
        ↓
Calculate Remaining Distance
        ↓
Run ETA Prediction
        ↓
Check Delay
        ↓
Save Tracking Event
        ↓
Repeat
```

The current hackathon configuration updates active simulated trucks every few seconds.

---

# 3. Manual Simulation Step

## Endpoint

```http
POST /simulation/step/{delivery_id}
```

Moves a simulated truck by one manual step.

---

## Important

This endpoint is mainly useful for:

* Manual Swagger testing
* Debugging
* Demonstrating a single movement step

It is **not required for normal frontend live tracking** because the backend background loop automatically moves active trucks.

The frontend should not continuously call this endpoint to make the marker move.

---

## Path Parameter

| Parameter     | Type    | Required | Description                                |
| ------------- | ------- | -------- | ------------------------------------------ |
| `delivery_id` | integer | Yes      | Active delivery to move one simulated step |

---

## Example Request

```http
POST /simulation/step/3
```

---

## Possible Error

If simulation is not active:

```json
{
  "detail": "Simulation is not active for this delivery"
}
```

---

## Example Successful Response

```json
{
  "message": "Simulation step completed",
  "delivery_id": 3,
  "tracking_number": "TRK-E2-101",
  "trailer_id": "TRL-101",
  "status": "in_transit",
  "current_latitude": 25.45,
  "current_longitude": 75.31,
  "current_location": "25.45000, 75.31000",
  "average_speed_kmph": 52.5,
  "distance_remaining_km": 320.4,
  "eta_minutes": 366.2,
  "estimated_arrival": "2026-08-26T11:00:00",
  "simulation_active": true
}
```

---

# 4. Stop GPS Simulation

## Endpoint

```http
POST /simulation/stop/{delivery_id}
```

Manually stops GPS simulation for a delivery.

---

## Path Parameter

| Parameter     | Type    | Required | Description                           |
| ------------- | ------- | -------- | ------------------------------------- |
| `delivery_id` | integer | Yes      | Delivery whose simulation should stop |

---

## Example Request

```http
POST /simulation/stop/3
```

---

## Example Response

```json
{
  "message": "Simulation stopped",
  "delivery_id": 3,
  "status": "in_transit",
  "simulation_active": false
}
```

---

# 5. Automatic Arrival Detection

The backend automatically detects when the truck reaches the warehouse or yard gate.

When the remaining distance is within the arrival threshold:

```text
Truck reaches destination
        ↓
Coordinates snap to destination
        ↓
current_location = Yard Gate
        ↓
status = arrived_at_gate
        ↓
actual_arrival = current time
        ↓
distance_remaining_km = 0
        ↓
eta_minutes = 0
        ↓
simulation_active = false
```

No manual stop request is required after successful arrival.

---

## Example Final Tracking State

```json
{
  "status": "arrived_at_gate",
  "current_latitude": 23.0225,
  "current_longitude": 72.5714,
  "current_location": "Yard Gate",
  "distance_remaining_km": 0,
  "eta_minutes": 0,
  "simulation_active": false
}
```

---

# 6. Simulated WMS Feed

## Endpoint

```http
GET /simulation/wms-feed
```

Returns the simulated Warehouse Management System feed.

The feed combines current trailer information and dock information for operations use.

---

## Example Request

```http
GET /simulation/wms-feed
```

---

## Response Contains

### Summary

```text
total_trailers
active_shipments
delayed_shipments
waiting_for_dock
total_docks
available_docks
```

### Trailer Information

```text
delivery_id
tracking_number
trailer_id
shipment_reference
carrier
trailer_status
yard_location
scheduled_arrival
estimated_arrival
actual_arrival
eta_minutes
current_latitude
current_longitude
distance_remaining_km
delay_detected
exception_detected
simulation_active
assigned_dock
```

### Dock Information

```text
dock_id
yard_name
dock_number
status
dock_type
supported_vehicle_type
max_vehicle_length
refrigerated
hazardous_allowed
```

---

## Example Response Structure

```json
{
  "feed_type": "SIMULATED_WMS",
  "generated_at": "2026-08-26T10:00:00",
  "summary": {
    "total_trailers": 3,
    "active_shipments": 2,
    "delayed_shipments": 1,
    "waiting_for_dock": 0,
    "total_docks": 2,
    "available_docks": 1
  },
  "trailers": [],
  "docks": []
}
```

---

# 7. Frontend Integration

For the frontend map, use the following recommended flow.

## Step 1

Start the simulation once:

```http
POST /simulation/start/{delivery_id}
```

---

## Step 2

Poll the tracking endpoint periodically:

```http
GET /tracking/shipment/id/{delivery_id}
```

For example, every few seconds.

---

## Step 3

Read:

```text
current_latitude
current_longitude
distance_remaining_km
eta_minutes
estimated_arrival
status
simulation_active
```

---

## Step 4

Update the frontend map marker using:

```text
current_latitude
current_longitude
```

---

## Step 5

Stop polling or change UI behavior when:

```text
simulation_active = false
```

and:

```text
status = arrived_at_gate
```

---

# 8. Simulated Real-Time Meaning

The correct project terminology is:

```text
Simulated real-time GPS tracking
```

The truck coordinates are generated automatically by the backend.

The system is not receiving GPS information from a physical truck.

However, once simulation starts, location values change dynamically over time and can be consumed by the frontend exactly like an incoming tracking feed.

---

# 9. Production Replacement

In a production logistics system, the simulation source could be replaced with:

* GPS devices
* Vehicle telematics systems
* Carrier APIs
* Fleet-management systems
* Transportation Management Systems
* IoT tracking platforms

The remaining backend flow can continue to process:

```text
Incoming Location
        ↓
Distance
        ↓
ETA
        ↓
Delay Detection
        ↓
Alerts
        ↓
Yard / Dock Operations
```

---

# 10. Hackathon Demo Recommendation

For a clean demo:

```text
1. Select one delivery
2. Start simulation once
3. Open the tracking/map view
4. Observe truck movement
5. Observe decreasing distance
6. Observe ETA updates
7. Show delay alert if triggered
8. Let truck reach Yard Gate
9. Show ETA = 0
10. Show distance = 0
11. Show simulation_active = false
```

Do not repeatedly press the simulation step endpoint during the final frontend demonstration.

---

# Summary

The Simulation API provides:

* Simulated GPS starting positions
* Automatic background truck movement
* Manual step testing
* Manual simulation stop
* Dynamic location updates
* Automatic arrival detection
* Simulated WMS feed
* Frontend-compatible coordinates
* Automatic simulation completion

The frontend should start a simulation once and then retrieve the latest tracking state while the backend handles movement automatically.
**
