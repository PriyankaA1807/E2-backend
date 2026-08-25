# Tracking API

The Tracking API provides shipment lookup, current shipment information, trailer/reference-based identification, historical tracking events, and active shipment retrieval for E2 Deliveries.

A frontend, PR2, or another backend service can identify the same shipment using:

- tracking number;
- E2 delivery ID;
- trailer ID;
- shipment reference.

The API also supports adding shipment events and retrieving chronological shipment history.

**Base path:** `/tracking`

---

# Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/tracking/shipment/{tracking_number}` | Get shipment by tracking number |
| GET | `/tracking/shipment/id/{delivery_id}` | Get shipment by E2 Delivery ID |
| GET | `/tracking/trailer/{trailer_id}` | Get shipment by trailer ID |
| GET | `/tracking/reference/{shipment_reference}` | Get shipment by shipment reference |
| POST | `/tracking/{delivery_id}/events` | Add a tracking event |
| GET | `/tracking/{delivery_id}/events` | Get shipment event history |
| GET | `/tracking/active` | Get active shipments |

---

# Tracking Architecture

E2 stores shipment tracking in two related forms.

```text
Delivery
   │
   ├── Identification
   │     ├── tracking_number
   │     ├── trailer_id
   │     └── shipment_reference
   │
   ├── Latest shipment state
   │     ├── current_location
   │     ├── current_latitude
   │     ├── current_longitude
   │     ├── status
   │     ├── ETA
   │     └── last_gps_update
   │
   └── TrackingEvents
         ├── Event 1
         ├── Event 2
         ├── Event 3
         └── ...
```

The **Delivery** represents the latest known shipment state.

**TrackingEvents** represent the historical shipment timeline.

This distinction is important when integrating:

```text
Live Map
Shipment Detail
Shipment Search
Timeline
PR2 Shipment Integration
```

---

# 1. Get Shipment by Tracking Number

## Endpoint

```http
GET /tracking/shipment/{tracking_number}
```

Returns the Delivery associated with a shipment tracking number.

---

## Path Parameter

| Parameter | Type | Required | Description |
|---|---|---:|---|
| `tracking_number` | string | Yes | Shipment tracking number |

---

## Example Request

```http
GET /tracking/shipment/TRK-PR2-TEST-001
```

---

## Backend Logic

```text
Receive tracking number
        ↓
Search Delivery
        ↓
Delivery found?
   ┌────┴────┐
   No       Yes
   ↓         ↓
  404   Return Delivery
```

---

## Successful Response

```http
200 OK
```

Example:

```json
{
  "restock_order_id": 3,
  "dock_id": null,
  "tracking_number": "TRK-PR2-TEST-001",
  "trailer_id": "TRL-PR2-001",
  "shipment_reference": "SHIP-PR2-001",
  "carrier": "BlueDart",
  "status": "scheduled",
  "scheduled_arrival": "2026-08-27T18:00:00",
  "actual_arrival": null,
  "current_latitude": null,
  "current_longitude": null,
  "current_location": null,
  "destination_latitude": 23.0225,
  "destination_longitude": 72.5714,
  "estimated_arrival": null,
  "eta_minutes": null,
  "average_speed_kmph": 50,
  "distance_remaining_km": null,
  "simulation_active": false,
  "id": 4,
  "delay_detected": false,
  "exception_detected": false,
  "last_gps_update": null
}
```

The exact response follows the Delivery response schema.

---

# 2. Get Shipment by Delivery ID

## Endpoint

```http
GET /tracking/shipment/id/{delivery_id}
```

Returns shipment information using E2's internal Delivery ID.

---

## Path Parameter

| Parameter | Type | Required | Description |
|---|---|---:|---|
| `delivery_id` | integer | Yes | Internal E2 Delivery ID |

---

## Example Request

```http
GET /tracking/shipment/id/4
```

---

## Successful Response

```http
200 OK
```

Returns the Delivery object.

---

## Delivery Not Found

```http
404 Not Found
```

---

# 3. Get Shipment by Trailer ID

## Endpoint

```http
GET /tracking/trailer/{trailer_id}
```

Returns the shipment currently associated with a trailer ID.

This endpoint is useful when the yard, PR2, WMS-like systems, or another logistics service identifies the physical vehicle before using the shipment tracking number.

---

## Path Parameter

| Parameter | Type | Required | Description |
|---|---|---:|---|
| `trailer_id` | string | Yes | Trailer or truck identifier |

---

## Example Request

```http
GET /tracking/trailer/TRL-PR2-001
```

---

## Successful Response

```http
200 OK
```

Example:

```json
{
  "restock_order_id": 3,
  "dock_id": null,
  "tracking_number": "TRK-PR2-TEST-001",
  "trailer_id": "TRL-PR2-001",
  "shipment_reference": "SHIP-PR2-001",
  "carrier": "BlueDart",
  "status": "scheduled",
  "scheduled_arrival": "2026-08-27T18:00:00",
  "actual_arrival": null,
  "current_latitude": null,
  "current_longitude": null,
  "current_location": null,
  "destination_latitude": 23.0225,
  "destination_longitude": 72.5714,
  "estimated_arrival": null,
  "eta_minutes": null,
  "average_speed_kmph": 50,
  "distance_remaining_km": null,
  "simulation_active": false,
  "id": 4,
  "delay_detected": false,
  "exception_detected": false,
  "last_gps_update": null
}
```

---

## Use Case

```text
Trailer arrives / is identified
          ↓
Read trailer ID
          ↓
GET /tracking/trailer/{trailer_id}
          ↓
Resolve E2 Delivery
          ↓
Tracking / ETA / Yard / Dock Operations
```

---

# 4. Get Shipment by Shipment Reference

## Endpoint

```http
GET /tracking/reference/{shipment_reference}
```

Returns the Delivery associated with an external or internal shipment reference.

This is especially useful for PR2 → E2 integration because PR2 can retain its shipment reference while E2 uses its own internal Delivery ID.

---

## Path Parameter

| Parameter | Type | Required | Description |
|---|---|---:|---|
| `shipment_reference` | string | Yes | Shipment reference received from another system or business workflow |

---

## Example Request

```http
GET /tracking/reference/SHIP-PR2-001
```

---

## Successful Response

```http
200 OK
```

Example:

```json
{
  "restock_order_id": 3,
  "dock_id": null,
  "tracking_number": "TRK-PR2-TEST-001",
  "trailer_id": "TRL-PR2-001",
  "shipment_reference": "SHIP-PR2-001",
  "carrier": "BlueDart",
  "status": "scheduled",
  "scheduled_arrival": "2026-08-27T18:00:00",
  "actual_arrival": null,
  "current_latitude": null,
  "current_longitude": null,
  "current_location": null,
  "destination_latitude": 23.0225,
  "destination_longitude": 72.5714,
  "estimated_arrival": null,
  "eta_minutes": null,
  "average_speed_kmph": 50,
  "distance_remaining_km": null,
  "simulation_active": false,
  "id": 4,
  "delay_detected": false,
  "exception_detected": false,
  "last_gps_update": null
}
```

---

# Identifier Strategy

E2 supports multiple shipment identifiers because different systems may know the shipment using different keys.

```text
Tracking Number
      │
      ├──────────────┐
      │              │
Trailer ID      Shipment Reference
      │              │
      └──────┬───────┘
             ↓
          Delivery
             ↓
     E2 Internal ID
```

## Recommended Usage

Use:

```text
tracking_number
```

for carrier/logistics tracking.

Use:

```text
trailer_id
```

for physical yard/trailer operations.

Use:

```text
shipment_reference
```

for external-system or business correlation.

Use:

```text
delivery_id
```

for internal E2 API operations.

---

# PR2 Integration Relationship

PR2 can create a shipment through:

```http
POST /integrations/shipments
```

Example request identifiers:

```json
{
  "external_order_id": "PO-PR2-TEST-001",
  "tracking_number": "TRK-PR2-TEST-001",
  "trailer_id": "TRL-PR2-001",
  "shipment_reference": "SHIP-PR2-001"
}
```

After import, PR2 or another system can verify the same E2 shipment through:

```http
GET /tracking/shipment/TRK-PR2-TEST-001
```

or:

```http
GET /tracking/trailer/TRL-PR2-001
```

or:

```http
GET /tracking/reference/SHIP-PR2-001
```

All should resolve to the same E2 Delivery.

---

# 5. Add Tracking Event

## Endpoint

```http
POST /tracking/{delivery_id}/events
```

Creates a historical tracking event for a Delivery.

The endpoint also updates the Delivery's latest shipment state.

---

## Path Parameter

| Parameter | Type | Required |
|---|---|---:|
| `delivery_id` | integer | Yes |

---

## Request

**Content-Type:**

```text
application/json
```

Example:

```json
{
  "status": "in_transit",
  "location": "Kolkata",
  "latitude": 22.5726,
  "longitude": 88.3639,
  "event_time": "2026-08-25T12:00:00",
  "description": "Shipment reached Kolkata"
}
```

---

# Tracking Event Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `status` | string | Yes | Shipment status associated with the event |
| `location` | string / null | No | Human-readable location |
| `latitude` | float / null | No | GPS latitude |
| `longitude` | float / null | No | GPS longitude |
| `event_time` | datetime / null | No | Time associated with event |
| `description` | string / null | No | Additional event information |

---

# Tracking Event Backend Logic

```text
POST Tracking Event
        ↓
Find Delivery
        ↓
Delivery exists?
  No → HTTP 404
        ↓ Yes
Create TrackingEvent
        ↓
Update Delivery status
        ↓
Location supplied?
  Yes → Update current_location
        ↓
Latitude supplied?
  Yes → Update current_latitude
        ↓
Longitude supplied?
  Yes → Update current_longitude
        ↓
Update last_gps_update
        ↓
Commit
        ↓
Return TrackingEvent
```

This keeps current Delivery information synchronized with explicitly submitted tracking events.

---

# Side Effects

Calling:

```http
POST /tracking/{delivery_id}/events
```

can change the associated Delivery.

Example request:

```json
{
  "status": "in_transit",
  "location": "Kolkata",
  "latitude": 22.5726,
  "longitude": 88.3639
}
```

Conceptually results in:

```text
TrackingEvent created
        +
Delivery.status = in_transit
Delivery.current_location = Kolkata
Delivery.current_latitude = 22.5726
Delivery.current_longitude = 88.3639
Delivery.last_gps_update = updated
```

Therefore another service does not need to separately update the Delivery location after submitting the event.

---

# Successful Tracking Event Response

```http
201 Created
```

Example:

```json
{
  "id": 15,
  "delivery_id": 2,
  "status": "in_transit",
  "location": "Kolkata",
  "latitude": 22.5726,
  "longitude": 88.3639,
  "event_time": "2026-08-25T12:00:00",
  "description": "Shipment reached Kolkata"
}
```

---

# 6. Get Tracking History

## Endpoint

```http
GET /tracking/{delivery_id}/events
```

Returns all TrackingEvents associated with a Delivery.

---

## Path Parameter

| Parameter | Type | Required |
|---|---|---:|
| `delivery_id` | integer | Yes |

---

## Example

```http
GET /tracking/2/events
```

---

# Event Ordering

TrackingEvents are returned in chronological order:

```text
event_time ASC
```

Oldest event appears first.

Newest event appears last.

Example:

```text
Shipment Created
       ↓
Siliguri Highway
       ↓
Kolkata
       ↓
Destination Yard
       ↓
Arrived at Gate
```

---

# Tracking History Example

```json
[
  {
    "id": 10,
    "delivery_id": 2,
    "status": "in_transit",
    "location": "Siliguri Highway",
    "latitude": 26.7271,
    "longitude": 88.3953,
    "event_time": "2026-08-24T10:00:00",
    "description": "Shipment in transit"
  },
  {
    "id": 11,
    "delivery_id": 2,
    "status": "in_transit",
    "location": "Kolkata",
    "latitude": 22.5726,
    "longitude": 88.3639,
    "event_time": "2026-08-24T15:00:00",
    "description": "Shipment reached Kolkata"
  }
]
```

---

# 7. Get Active Shipments

## Endpoint

```http
GET /tracking/active
```

Returns Deliveries whose current status is considered operationally active.

The E2 lifecycle now includes operational states such as:

```text
scheduled
in_transit
delayed
arrived_at_gate
in_yard
waiting_for_dock
dock_assigned
docked
unloading
```

Legacy test data may still contain:

```text
arrived
```

depending on when the record was created.

Completed/inactive states may include:

```text
completed
departed
delivered
cancelled
```

depending on lifecycle compatibility and historical data.

---

# Delivery Lifecycle

The current operational lifecycle is designed around yard and dock handling.

Typical flow:

```text
scheduled
   ↓
in_transit
   ↓
arrived_at_gate
   ↓
in_yard
   ↓
waiting_for_dock
   ↓
dock_assigned
   ↓
docked
   ↓
unloading
   ↓
completed / departed
```

Delay can be an operational condition during the shipment flow:

```text
in_transit
   ↓
delayed
```

Lifecycle validation prevents invalid transitions.

For example:

```text
arrived_at_gate
        ↓
completed
```

is rejected if the valid next state is:

```text
in_yard
```

---

# Tracking vs GPS Simulation

Tracking and Simulation work together but are separate modules.

## Tracking

Stores and retrieves shipment state and historical events.

## Simulation

Generates artificial GPS movement for testing and demonstration.

```text
Simulation
    ↓
GPS Movement
    ↓
Delivery Location
    ↓
ETA / Distance
    ↓
Tracking / Dashboard
```

Simulation is documented separately in:

```text
simulation-api.md
```

---

# Background Simulation Behavior

After GPS simulation starts, E2's background tracking loop can automatically update the Delivery's current GPS state.

However, background movement should not be treated as equivalent to the TrackingEvent timeline.

```text
Delivery
   ↓
Latest current GPS state
```

and:

```text
TrackingEvents
   ↓
Historical event timeline
```

serve different purposes.

---

# Manual Simulation Step

```http
POST /simulation/step/{delivery_id}
```

A manual simulation step can update shipment movement and may create a tracking event depending on the simulation implementation.

Tracking history can then be retrieved using:

```http
GET /tracking/{delivery_id}/events
```

---

# Live Map Integration

For a live map, the frontend should primarily use the Delivery's latest coordinates:

```text
current_latitude
current_longitude
current_location
```

The dashboard also provides:

```http
GET /dashboard/live-shipments
```

and:

```http
GET /dashboard/yard-status
```

for operational shipment visibility.

A frontend can poll these APIs while simulation is active.

---

# Yard Integration

Tracking identifiers can be used before or during yard operations.

Example:

```text
Trailer arrives at gate
        ↓
Read trailer_id
        ↓
GET /tracking/trailer/{trailer_id}
        ↓
Find Delivery
        ↓
Check shipment status
        ↓
Yard / Dock Workflow
```

This avoids requiring the yard operator to know E2's internal `delivery_id`.

---

# Dock Integration

After resolving the Delivery through tracking, dock-related operations can use the internal Delivery ID.

For example:

```text
GET /tracking/trailer/TRL-PR2-001
        ↓
delivery_id = 4
        ↓
GET /dock-operations/recommend/4
```

or:

```text
GET /dashboard/trailer-door-allocation
```

---

# Shipment Timeline Integration

For a shipment-history component:

```text
Shipment Detail Page
        ↓
GET /tracking/{delivery_id}/events
        ↓
Receive events
        ↓
Ordered by event_time
        ↓
Render timeline
```

Example frontend timeline:

```text
● Shipment Created
│
● In Transit
│
● Kolkata
│
● Arrived at Gate
│
● Dock Assigned
```

---

# Cross-Team Integration

Another backend can use E2 Tracking without knowing Python, SQLAlchemy, or FastAPI internals.

The external system only needs the HTTP contract.

For example:

```http
POST /tracking/4/events
```

with:

```json
{
  "status": "in_transit",
  "location": "Kolkata",
  "latitude": 22.5726,
  "longitude": 88.3639,
  "event_time": "2026-08-25T12:00:00",
  "description": "GPS update received"
}
```

E2 handles:

```text
Create TrackingEvent
        +
Update Delivery state
```

---

# Relationship with Integrations API

The Integrations API creates an E2 shipment from PR2 or another external service.

```text
PR2
 ↓
POST /integrations/shipments
 ↓
E2 Delivery
 ↓
Tracking APIs
```

See:

```text
integrations-api.md
```

for the external shipment creation contract.

---

# Relationship with Operations

Tracking information is also used for operational exception detection.

Example:

```text
Delivery status = in_transit
        +
No GPS update received
        ↓
Exception Detection
        ↓
Shipment Exception
        ↓
Operational Alert
```

See:

```text
operations-api.md
```

for operational checks.

---

# Relationship with ETA

Current shipment position and remaining distance can be used by ETA logic.

Conceptually:

```text
Tracking / GPS
      ↓
Current Position
      ↓
Distance Remaining
      ↓
ETA Prediction
      ↓
Estimated Arrival
```

See:

```text
eta-api.md
```

for ETA details.

---

# Error Handling

Frontend and integrating services should handle:

| HTTP Status | Meaning |
|---:|---|
| `200` | Successful shipment/event retrieval |
| `201` | TrackingEvent created |
| `404` | Shipment / Delivery not found |
| `422` | Request or path validation failed |
| `500` | Unexpected backend error |

FastAPI errors generally follow:

```json
{
  "detail": "Error message"
}
```

---

# Example Integration Test

After PR2 imports:

```json
{
  "external_order_id": "PO-PR2-TEST-001",
  "tracking_number": "TRK-PR2-TEST-001",
  "trailer_id": "TRL-PR2-001",
  "shipment_reference": "SHIP-PR2-001"
}
```

verify:

```http
GET /tracking/shipment/TRK-PR2-TEST-001
```

then:

```http
GET /tracking/trailer/TRL-PR2-001
```

then:

```http
GET /tracking/reference/SHIP-PR2-001
```

All should resolve to the same E2 Delivery.

---

# Frontend Recommendations

## Shipment Search

Allow users to search using:

```text
Tracking Number
Trailer ID
Shipment Reference
```

## Live Shipment View

Use:

```http
GET /dashboard/live-shipments
```

or:

```http
GET /dashboard/yard-status
```

## Timeline

Use:

```http
GET /tracking/{delivery_id}/events
```

## Yard / Trailer Search

Use:

```http
GET /tracking/trailer/{trailer_id}
```

## External Shipment Correlation

Use:

```http
GET /tracking/reference/{shipment_reference}
```

---

# Current Limitations

The current Tracking API does not provide:

- WebSocket shipment streaming;
- Socket.IO tracking events;
- Server-Sent Events;
- real GPS-provider integration;
- pagination for TrackingEvent history.

Live movement currently relies on simulation and HTTP polling.

Do not treat TrackingEvent history as a frame-by-frame GPS stream.

For latest position use:

```text
Current Delivery
/dashboard/live-shipments
/dashboard/yard-status
```

For historical events use:

```http
GET /tracking/{delivery_id}/events
```

---

# Summary

The Tracking API acts as the identification and shipment-state layer of E2.

```text
Tracking Number
Trailer ID
Shipment Reference
Delivery ID
        ↓
     Delivery
        ↓
Latest Shipment State
        +
Tracking History
```

It supports frontend tracking, PR2 integration, yard identification, ETA processing, exception detection, and downstream dock operations.
