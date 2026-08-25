# GPS & Simulation API

The GPS & Simulation API simulates shipment movement for an E2 Delivery and exposes a simulated WMS-style operational feed.

It allows E2 to demonstrate:

- live shipment movement;
- GPS updates;
- remaining-distance calculation;
- speed variation;
- ETA updates;
- shipment arrival behavior;
- trailer/yard visibility;
- dock assignment state;
- simulated WMS integration.

**Base path:** `/simulation`

---

# Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/simulation/start/{delivery_id}` | Start GPS simulation |
| POST | `/simulation/step/{delivery_id}` | Manually advance one simulation step |
| POST | `/simulation/stop/{delivery_id}` | Stop GPS simulation |
| GET | `/simulation/wms-feed` | Get simulated WMS-style trailer/dock feed |

---

# Simulation Architecture

```text
Delivery
   ↓
Start Simulation
   ↓
simulation_active = true
   ↓
Background Tracking Loop
   ↓
GPS Movement
   ↓
Distance Remaining
   ↓
Speed
   ↓
ETA
   ↓
Estimated Arrival
   ↓
Operational State
   ↓
Dashboard / Tracking / WMS Feed
```

The frontend does not need to call `/step` repeatedly for normal automatic simulation.

---

# 1. Start GPS Simulation

## Endpoint

```http
POST /simulation/start/{delivery_id}
```

Starts simulated GPS tracking for an existing Delivery.

---

## Path Parameter

| Parameter | Type | Required | Description |
|---|---|---:|---|
| `delivery_id` | integer | Yes | Delivery to simulate |

---

## Example Request

```http
POST /simulation/start/2
```

No request body is required.

---

# Backend Logic

```text
Receive delivery_id
      ↓
Find Delivery
      ↓
Delivery exists?
  No → 404
      ↓ Yes
Check / initialize coordinates
      ↓
simulation_active = true
      ↓
status = in_transit
      ↓
last_gps_update = current UTC
      ↓
Commit
      ↓
Return confirmation
```

---

# Default Coordinates

The simulation requires:

```text
current_latitude
current_longitude
destination_latitude
destination_longitude
```

If some values are missing, the current project logic can provide defaults so the shipment can still be used for demonstration.

---

# Example Successful Response

```json
{
  "message": "GPS simulation started",
  "delivery_id": 2,
  "status": "in_transit"
}
```

Starting simulation changes the operational state:

```text
Before

simulation_active = false

        ↓ START

After

simulation_active = true
status = in_transit
last_gps_update = current time
```

---

# Delivery Not Found

If the Delivery does not exist:

```http
404 Not Found
```

---

# Automatic Background Simulation

The FastAPI application starts a background tracking loop during application startup.

Conceptually:

```text
Application Starts
      ↓
tracking_background_loop()
      ↓
Find Deliveries where simulation_active = true
      ↓
Update shipment movement periodically
```

Once:

```text
simulation_active = true
```

the background process can continue updating the Delivery without repeated frontend movement requests.

---

# What Background Simulation Updates

The background process can update:

```text
current_latitude
current_longitude
current_location
last_gps_update
average_speed_kmph
distance_remaining_km
eta_minutes
estimated_arrival
status
actual_arrival
simulation_active
```

These fields represent the latest simulated shipment state.

---

# Simulated Movement

The shipment moves gradually toward its destination.

```text
Current GPS
    ↓
Movement Step
    ↓
New GPS
    ↓
Movement Step
    ↓
New GPS
    ↓
Destination
```

Small coordinate variations can be introduced so movement appears more realistic.

---

# Distance Calculation

Conceptually:

```text
Current GPS
     +
Destination GPS
     ↓
Distance Calculation
     ↓
distance_remaining_km
```

The result is stored on the Delivery.

---

# Speed and ETA

The simulation uses the current/simulated speed to calculate remaining travel time.

```text
distance_remaining_km
          ÷
average_speed_kmph
          ↓
Remaining Hours
          ↓
ETA Minutes
          ↓
Estimated Arrival
```

The result is stored in:

```text
eta_minutes
estimated_arrival
```

---

# Simulation ETA vs ML ETA

E2 contains two ETA mechanisms.

## Simulation ETA

Uses:

```text
Remaining Distance
        ÷
Speed
        ↓
Travel Time
```

## ML ETA

Uses:

```text
Distance
Quantity
Supplier Delay History
Carrier Delay History
        ↓
RandomForestRegressor
```

Available through:

```http
GET /eta/predict
```

and:

```http
POST /eta/predict-delivery/{delivery_id}
```

The background simulator does not necessarily run the Random Forest model on every movement update.

---

# 2. Manual Simulation Step

## Endpoint

```http
POST /simulation/step/{delivery_id}
```

Moves the shipment forward by one simulation step immediately.

This is useful for controlled testing.

---

## Example Request

```http
POST /simulation/step/2
```

---

# Requirement

The Delivery must have:

```text
simulation_active = true
```

Conceptually:

```text
POST /simulation/step/{id}
      ↓
Find Delivery
      ↓
simulation_active?
  No → Error
      ↓ Yes
Perform one movement step
```

---

# Manual Step Logic

```text
Current GPS
     ↓
Move toward destination
     ↓
Generate/update speed
     ↓
Calculate remaining distance
     ↓
Calculate ETA
     ↓
Update Delivery
     ↓
Create TrackingEvent
     ↓
Check arrival
     ↓
Commit
```

---

# TrackingEvent Side Effect

The manual step can create a TrackingEvent representing the movement.

That event can then be retrieved through:

```http
GET /tracking/{delivery_id}/events
```

---

# Background Movement vs Manual Step

| Behavior | Background Simulation | Manual `/step` |
|---|---:|---:|
| Updates GPS | Yes | Yes |
| Updates distance | Yes | Yes |
| Updates speed | Yes | Yes |
| Updates ETA | Yes | Yes |
| Updates Delivery | Yes | Yes |
| Creates TrackingEvent for every movement | No | Yes |
| Requires frontend movement call | No | Yes |

---

# Arrival Detection

After movement, the backend checks whether the shipment is sufficiently close to its destination.

```text
Remaining Distance
      ↓
Within Arrival Threshold?
   ┌──────┴──────┐
   No            Yes
    ↓             ↓
Continue      Arrival Processing
```

Arrival processing can update:

```text
actual_arrival
status
simulation_active
distance_remaining_km
eta_minutes
```

The exact lifecycle status depends on the current delivery workflow.

For newer yard-oriented shipments, arrival-related statuses may include:

```text
arrived_at_gate
```

while older records may still contain:

```text
arrived
```

---

# 3. Stop GPS Simulation

## Endpoint

```http
POST /simulation/stop/{delivery_id}
```

Stops automatic simulation for a Delivery.

---

## Example Request

```http
POST /simulation/stop/2
```

The backend sets:

```text
simulation_active = false
```

The background loop should then stop moving that shipment.

---

# 4. Simulated WMS Feed

## Endpoint

```http
GET /simulation/wms-feed
```

Returns a simulated Warehouse Management System style feed containing operational trailer and dock information.

This endpoint is useful for:

- frontend integration;
- PR2/WMS-style testing;
- yard operations demonstrations;
- trailer visibility;
- dock availability monitoring.

---

# Example Request

```http
GET /simulation/wms-feed
```

No request body or query parameters are required.

---

# Example Successful Response

```json
{
  "feed_type": "SIMULATED_WMS",
  "generated_at": "2026-08-25T13:15:06.540483",
  "summary": {
    "total_trailers": 3,
    "active_shipments": 3,
    "delayed_shipments": 1,
    "waiting_for_dock": 0,
    "total_docks": 2,
    "available_docks": 1
  },
  "trailers": [
    {
      "delivery_id": 3,
      "tracking_number": "TRK-E2-101",
      "trailer_id": "TRL-101",
      "shipment_reference": "SHIP-E2-101",
      "carrier": "BlueDart",
      "trailer_status": "arrived_at_gate",
      "yard_location": null,
      "scheduled_arrival": "2026-08-25T15:00:00",
      "estimated_arrival": null,
      "actual_arrival": "2026-08-25T12:59:24.029154",
      "eta_minutes": null,
      "current_latitude": null,
      "current_longitude": null,
      "distance_remaining_km": null,
      "delay_detected": false,
      "exception_detected": false,
      "simulation_active": false,
      "assigned_dock": {
        "dock_id": 1,
        "dock_number": "D-01",
        "yard_name": "Main Warehouse",
        "status": "available",
        "dock_type": "standard"
      }
    }
  ],
  "docks": [
    {
      "dock_id": 1,
      "yard_name": "Main Warehouse",
      "dock_number": "D-01",
      "status": "available",
      "dock_type": "standard",
      "supported_vehicle_type": "truck",
      "max_vehicle_length": 20,
      "refrigerated": false,
      "hazardous_allowed": false
    }
  ]
}
```

---

# WMS Feed Summary

The `summary` object contains:

| Field | Type | Description |
|---|---|---|
| `total_trailers` | integer | Total trailers/Deliveries included |
| `active_shipments` | integer | Operationally active shipments |
| `delayed_shipments` | integer | Shipments currently flagged delayed |
| `waiting_for_dock` | integer | Shipments waiting for dock allocation |
| `total_docks` | integer | Total YardDock records |
| `available_docks` | integer | Docks currently available |

---

# WMS Trailer Object

A trailer entry can include:

| Field | Description |
|---|---|
| `delivery_id` | E2 Delivery ID |
| `tracking_number` | Shipment tracking number |
| `trailer_id` | Trailer identifier |
| `shipment_reference` | Shipment reference |
| `carrier` | Logistics carrier |
| `trailer_status` | Current Delivery/trailer status |
| `yard_location` | Current known location |
| `scheduled_arrival` | Planned arrival |
| `estimated_arrival` | Estimated arrival |
| `actual_arrival` | Actual arrival |
| `eta_minutes` | Remaining ETA |
| `current_latitude` | Current latitude |
| `current_longitude` | Current longitude |
| `distance_remaining_km` | Remaining distance |
| `delay_detected` | Delay flag |
| `exception_detected` | Exception flag |
| `simulation_active` | Simulation state |
| `assigned_dock` | Current assigned dock |

---

# Assigned Dock Object

Example:

```json
{
  "dock_id": 2,
  "dock_number": "D-01",
  "yard_name": "Kolkata Main Yard",
  "status": "reserved",
  "dock_type": "standard"
}
```

If the Delivery has no dock:

```json
"assigned_dock": null
```

---

# WMS Dock Object

The dock list can include:

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

This lets another frontend/service obtain both:

```text
Incoming Trailers
+
Current Dock Capacity
```

from one endpoint.

---

# WMS Feed Architecture

```text
Deliveries
    │
    ├── Tracking
    ├── ETA
    ├── Status
    ├── Delay / Exception Flags
    └── Dock Assignment
    │
Yard Docks
    │
    ├── Availability
    ├── Type
    └── Capabilities
    │
    ▼
GET /simulation/wms-feed
    │
    ▼
Simulated WMS Payload
    │
    ├── Summary
    ├── Trailers
    └── Docks
```

---

# Why a Simulated WMS Feed Exists

E2 does not require a real external Warehouse Management System during development.

The simulated feed provides a stable integration contract for:

- UI development;
- cross-team testing;
- yard/dock demonstrations;
- future real WMS replacement.

Conceptually:

```text
Current Project

E2 Database
    ↓
Simulated WMS Feed
    ↓
Frontend / Other Service
```

A future production system could replace the simulated source with a real WMS or event stream while preserving similar downstream concepts.

---

# PR2 / External Integration Relationship

PR2 can create a shipment through:

```http
POST /integrations/shipments
```

That shipment becomes a normal E2 Delivery.

It can then appear in:

```http
GET /simulation/wms-feed
```

along with other active shipments.

Conceptually:

```text
PR2
 ↓
Integration API
 ↓
E2 Delivery
 ↓
WMS Feed
 ↓
Yard / Dock UI
```

---

# Relationship with Yard Status

The Dashboard API also provides:

```http
GET /dashboard/yard-status
```

The difference is:

## WMS Feed

Provides a broad simulated external-system-style feed:

```text
Trailers + Docks
```

## Yard Status

Provides a frontend-oriented operational yard view:

```text
Operational State
At Gate
In Yard
Waiting for Dock
Assigned Dock
Delayed
```

---

# Relationship with Dock Schedule

The WMS feed shows current dock assignment and capacity.

For planned time-window scheduling, use:

```http
GET /dashboard/dock-schedule
```

or:

```http
GET /dock-operations/schedule
```

---

# Frontend Live-Tracking Integration

For normal automatic simulation:

```text
Shipment Detail
      ↓
POST /simulation/start/{delivery_id}
      ↓
Background movement
      ↓
Frontend polls
      │
      ├── /dashboard/live-shipments
      ├── /dashboard/yard-status
      └── /simulation/wms-feed
      ↓
Update UI
```

---

# Reading Current Position

For current shipment information, use:

```http
GET /dashboard/live-shipments
```

or shipment-specific Tracking/Delivery endpoints.

The WMS feed can also provide current GPS fields when available.

---

# Shipment History

For historical events use:

```http
GET /tracking/{delivery_id}/events
```

Remember:

```text
Current Position
      ≠
Tracking History
```

The background loop updates current Delivery state but does not create a new TrackingEvent for every automatic GPS movement.

---

# Cross-Team Integration

Another team does not need to reproduce simulation logic.

It can simply:

```text
1. Obtain delivery_id

2. POST /simulation/start/{delivery_id}

3. Poll:
   /simulation/wms-feed
   or
   /dashboard/live-shipments

4. Stop with:
   POST /simulation/stop/{delivery_id}
```

All movement, distance, and simulation ETA calculations stay inside E2.

---

# Error Handling

Integrating applications should handle:

| HTTP Status | Meaning |
|---:|---|
| `200` | Simulation/feed request completed |
| `400` | Simulation operation invalid for current state |
| `404` | Delivery not found |
| `422` | Invalid Delivery ID/path validation |
| `500` | Unexpected simulation/database failure |

FastAPI errors typically use:

```json
{
  "detail": "Error message"
}
```

---

# Current Limitations

The current simulation system:

- uses simulated GPS instead of a real telematics provider;
- uses HTTP polling instead of WebSockets;
- does not create TrackingEvents for every background movement;
- uses speed/distance ETA during simulation rather than calling Random Forest on every update;
- requires simulation to be explicitly started;
- exposes a simulated WMS feed rather than connecting to a real WMS;
- does not yet publish events to Kafka/RabbitMQ;
- does not provide production-grade telematics authentication.

---

# Summary

The Simulation module supports both shipment movement and external-style operational feed testing.

```text
Delivery
   ↓
GPS Simulation
   ↓
Current Position
   ↓
Distance + ETA
   ↓
Tracking / Dashboard

and

Deliveries + Docks
        ↓
GET /simulation/wms-feed
        ↓
Simulated WMS Integration
```

Use simulation endpoints for movement testing and `/simulation/wms-feed` for combined trailer/dock operational visibility.
