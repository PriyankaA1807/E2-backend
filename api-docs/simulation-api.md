# GPS Simulation API

The GPS Simulation API simulates shipment movement for a Delivery.

It allows E2 to demonstrate live shipment tracking without requiring a real GPS device or external telematics provider.

Once simulation is started, the backend can update the Delivery's current location, distance, speed, ETA, and shipment status.

**Base path:** `/simulation`

---

## Endpoints

| Method | Endpoint                          | Purpose                                        |
| ------ | --------------------------------- | ---------------------------------------------- |
| POST   | `/simulation/start/{delivery_id}` | Start GPS simulation                           |
| POST   | `/simulation/step/{delivery_id}`  | Manually move the shipment one simulation step |
| POST   | `/simulation/stop/{delivery_id}`  | Stop GPS simulation                            |

---

# Simulation Workflow

```text
Delivery Created
      ↓
POST /simulation/start/{delivery_id}
      ↓
simulation_active = true
status = in_transit
      ↓
Background Tracking Loop
      ↓
GPS Position Updates
      ↓
Distance Remaining
      ↓
Speed
      ↓
ETA / Estimated Arrival
      ↓
Destination Reached
      ↓
Shipment Arrival
```

The frontend does not need to repeatedly call the manual `/step` endpoint for normal automatic simulation.

---

# Start GPS Simulation

## `POST /simulation/start/{delivery_id}`

Starts simulated GPS tracking for an existing Delivery.

### Path Parameter

| Parameter     | Type    | Required | Description          |
| ------------- | ------- | -------: | -------------------- |
| `delivery_id` | integer |      Yes | Delivery to simulate |

### Example Request

```http
POST /simulation/start/2
```

No request body is required.

---

# Backend Logic

The backend first retrieves the Delivery.

```text
Receive delivery_id
       ↓
Find Delivery
       ↓
Delivery exists?
 No → HTTP 404
       ↓ Yes
Check GPS coordinates
       ↓
Set defaults where required
       ↓
simulation_active = true
       ↓
status = in_transit
       ↓
last_gps_update = current UTC time
       ↓
Commit
       ↓
Return confirmation
```

---

# Default Coordinates

The simulation requires current and destination coordinates.

If required coordinates are missing when simulation starts, the current implementation supplies default coordinates so the simulator can operate.

This allows a Delivery without manually configured GPS coordinates to still be used in the demo simulation.

---

# Successful Response

Example:

```json
{
  "message": "GPS simulation started",
  "delivery_id": 2,
  "status": "in_transit"
}
```

Starting simulation changes the Delivery's operational state.

Conceptually:

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

**HTTP 404**

with a FastAPI error response.

---

# Automatic Background Simulation

Starting the simulation does not require the frontend to manually send every GPS update.

The FastAPI application starts a background tracking loop during application startup.

Conceptually:

```text
Application Starts
      ↓
tracking_background_loop()
      ↓
Find active simulated Deliveries
      ↓
Update their movement periodically
```

Once:

```text
simulation_active = true
```

the background process can continue updating that Delivery.

---

# What the Background Process Updates

During simulated movement, Delivery tracking information can be updated, including:

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
```

These values represent the latest simulated shipment state.

---

# Simulated Movement

The shipment is moved gradually from its current position toward its destination.

Conceptually:

```text
Current Position
      │
      │ movement
      ▼
New Position
      │
      │ movement
      ▼
New Position
      │
      ▼
Destination
```

The simulation also introduces small variation to make the GPS movement behave more like changing shipment coordinates rather than instantly jumping to the destination.

---

# Distance Calculation

After movement, the simulator calculates the remaining distance between the shipment and its destination.

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

The remaining distance is stored on the Delivery.

---

# Speed and ETA

The simulator generates/uses simulated shipment speed.

Using the remaining distance and speed, it calculates remaining travel time.

Conceptually:

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

The result is stored in Delivery fields such as:

```text
eta_minutes
estimated_arrival
```

---

# Important: Simulation ETA vs ML ETA

The ETA generated by GPS simulation is **not the same mechanism** as the machine-learning ETA endpoint.

Simulation uses movement information:

```text
Remaining Distance
        +
Speed
        ↓
Simulation ETA
```

The separate ML endpoint:

```http
GET /eta/predict
```

uses:

```text
Distance
Quantity
Supplier Delay History
Carrier Delay History
        ↓
Random Forest Model
        ↓
ML ETA
```

The simulation does not currently call the Random Forest model for every GPS update.

See `eta-api.md` for ML ETA documentation.

---

# Manual Simulation Step

## `POST /simulation/step/{delivery_id}`

Moves the shipment forward by one simulation step manually.

This endpoint is useful for testing or controlled demonstrations.

### Example Request

```http
POST /simulation/step/2
```

---

# Requirement

The Delivery must already have an active simulation.

Conceptually:

```text
POST /simulation/step/{id}
        ↓
Find Delivery
        ↓
simulation_active?
   No → Error
        ↓ Yes
Perform movement
```

---

# Manual Step Logic

A manual simulation step performs the movement calculations immediately.

```text
Current GPS
     ↓
Move toward destination
     ↓
Add simulated GPS variation
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

An important difference between manual stepping and automatic background movement is TrackingEvent creation.

Calling:

```http
POST /simulation/step/{delivery_id}
```

creates a TrackingEvent representing that simulation movement.

Therefore the event can later appear in:

```http
GET /tracking/{delivery_id}/events
```

---

# Automatic Movement vs Manual Step

| Behavior                                 | Background Simulation | `/simulation/step` |
| ---------------------------------------- | --------------------: | -----------------: |
| Updates current GPS                      |                   Yes |                Yes |
| Updates distance                         |                   Yes |                Yes |
| Updates speed                            |                   Yes |                Yes |
| Updates ETA                              |                   Yes |                Yes |
| Updates Delivery                         |                   Yes |                Yes |
| Creates TrackingEvent for the movement   |                    No |                Yes |
| Requires frontend call for each movement |                    No |                Yes |

This distinction is important for frontend integration.

---

# Arrival Detection

After each simulated movement, the backend checks whether the shipment has reached the coded arrival threshold.

When the shipment is close enough to the destination, the simulator can mark the Delivery as arrived.

Conceptually:

```text
Calculate Remaining Distance
        ↓
Within arrival threshold?
   No → Continue simulation
        ↓ Yes
Shipment reached destination
        ↓
Update arrival state
```

The exact arrival behavior is controlled by the simulation logic in the backend.

---

# Stop GPS Simulation

## `POST /simulation/stop/{delivery_id}`

Stops automatic simulation for a Delivery.

### Example Request

```http
POST /simulation/stop/2
```

The backend sets:

```text
simulation_active = false
```

After this, the background simulation should no longer move that Delivery as an active simulated shipment.

---

# Frontend Integration

For a normal live-tracking demo, the frontend can use:

```text
Shipment Detail
      ↓
POST /simulation/start/{delivery_id}
      ↓
Simulation starts
      ↓
Backend moves shipment automatically
      ↓
Frontend polls live shipment data
      ↓
Map marker changes position
```

The frontend does **not** need:

```text
POST /simulation/step
POST /simulation/step
POST /simulation/step
...
```

for normal automatic movement.

---

# Reading Live Position

For current shipment information, the frontend can use current Delivery data or:

```http
GET /dashboard/live-shipments
```

Conceptually:

```text
Background Simulator
        ↓
Updates Delivery
        ↓
GET /dashboard/live-shipments
        ↓
Frontend
        ↓
Update Map
```

Since the project currently does not use WebSockets, the frontend can periodically poll the relevant GET endpoint.

---

# Shipment History

For historical shipment events:

```http
GET /tracking/{delivery_id}/events
```

should be used.

Remember:

```text
Live Current Position
        ≠
Tracking Event History
```

The background simulator updates current Delivery state but does not create a TrackingEvent for every automatic GPS movement.

---

# Cross-Team Integration

Another frontend or backend does not need to reproduce the simulation algorithm.

It only needs to:

```text
1. Know delivery_id

2. POST /simulation/start/{delivery_id}

3. Read updated shipment state

4. POST /simulation/stop/{delivery_id}
   when required
```

The movement, distance and simulation ETA calculations remain inside E2.

---

# Error Handling

Integrating applications should handle:

| HTTP Status | Meaning                                                       |
| ----------: | ------------------------------------------------------------- |
|       `200` | Simulation operation completed                                |
|       `404` | Delivery does not exist                                       |
|       `400` | Simulation operation cannot be performed in the current state |
|       `422` | Invalid Delivery ID/path validation                           |

FastAPI HTTP errors use the normal form:

```json
{
  "detail": "Error message"
}
```

---

# Current Limitations

The current simulation system:

* Uses simulated GPS rather than a real GPS/telematics provider
* Uses HTTP polling rather than WebSockets
* Does not create a TrackingEvent for every automatic background movement
* Uses distance/speed-based ETA rather than the Random Forest model during movement
* Requires simulation to be started before automatic simulated tracking occurs

The simulation should therefore be treated as a **demo/testing implementation of live shipment movement**, while the Tracking and Delivery APIs provide the integration interface for consuming its results.
