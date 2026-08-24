# Tracking API

The Tracking API provides shipment lookup, current shipment information, and historical tracking events for Deliveries.

It allows another frontend or service to identify a shipment using either its **tracking number** or **Delivery ID**, add shipment events, retrieve the shipment timeline, and retrieve active shipments.

**Base path:** `/tracking`

---

## Endpoints

| Method | Endpoint                               | Purpose                         |
| ------ | -------------------------------------- | ------------------------------- |
| GET    | `/tracking/shipment/{tracking_number}` | Get shipment by tracking number |
| GET    | `/tracking/shipment/id/{delivery_id}`  | Get shipment by Delivery ID     |
| POST   | `/tracking/{delivery_id}/events`       | Add a Tracking Event            |
| GET    | `/tracking/{delivery_id}/events`       | Get shipment event history      |
| GET    | `/tracking/active`                     | Get active shipments            |

---

# Tracking Architecture

E2 stores shipment tracking in two related forms.

```text
Delivery
   │
   ├── Latest shipment state
   │     ├── current location
   │     ├── latitude
   │     ├── longitude
   │     ├── status
   │     └── last GPS update
   │
   └── TrackingEvents
         ├── Event 1
         ├── Event 2
         ├── Event 3
         └── ...
```

The **Delivery** represents the latest known state.

**TrackingEvents** represent the historical shipment timeline.

This distinction is important when integrating a live map and a shipment-history screen.

---

# Get Shipment by Tracking Number

## `GET /tracking/shipment/{tracking_number}`

Returns the Delivery associated with a tracking number.

### Path Parameter

| Parameter         | Type   | Required | Description              |
| ----------------- | ------ | -------: | ------------------------ |
| `tracking_number` | string |      Yes | Shipment tracking number |

### Example Request

```http
GET /tracking/shipment/TRK-10001
```

### Backend Logic

```text
Receive tracking number
        ↓
Search Delivery
        ↓
Delivery found?
   No → HTTP 404
        ↓ Yes
Return Delivery
```

### Successful Response

Returns the Delivery object containing its latest shipment state.

The response can contain information such as:

```json
{
  "id": 2,
  "restock_order_id": 1,
  "tracking_number": "TRK-10001",
  "carrier": "ABC Logistics",
  "status": "in_transit",
  "current_latitude": 22.5726,
  "current_longitude": 88.3639,
  "current_location": "Kolkata"
}
```

The exact response follows the Delivery response schema.

---

# Get Shipment by Delivery ID

## `GET /tracking/shipment/id/{delivery_id}`

Returns shipment information using E2's internal Delivery ID.

### Path Parameter

| Parameter     | Type    | Required |
| ------------- | ------- | -------: |
| `delivery_id` | integer |      Yes |

### Example Request

```http
GET /tracking/shipment/id/2
```

### Successful Response

Returns the Delivery object.

### Delivery Not Found

If the Delivery does not exist, the API returns HTTP `404`.

---

# Add Tracking Event

## `POST /tracking/{delivery_id}/events`

Creates a new historical tracking event for a Delivery.

This endpoint also updates the Delivery's latest shipment state.

### Path Parameter

| Parameter     | Type    | Required |
| ------------- | ------- | -------: |
| `delivery_id` | integer |      Yes |

### Request

**Content-Type:** `application/json`

Example:

```json
{
  "status": "in_transit",
  "location": "Kolkata",
  "latitude": 22.5726,
  "longitude": 88.3639,
  "event_time": "2026-08-25T00:00:00",
  "description": "Shipment reached Kolkata"
}
```

---

# Tracking Event Fields

| Field         | Type          | Description                               |
| ------------- | ------------- | ----------------------------------------- |
| `status`      | string        | Shipment status associated with the event |
| `location`    | string / null | Human-readable event location             |
| `latitude`    | float / null  | GPS latitude                              |
| `longitude`   | float / null  | GPS longitude                             |
| `event_time`  | datetime      | Time associated with the event            |
| `description` | string / null | Additional event description              |

The request fields follow the TrackingEvent creation schema used by the backend.

---

# Backend Logic

Creating a TrackingEvent does more than insert a history record.

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

This keeps the current Delivery state synchronized with the newest event submitted through this API.

---

# Side Effects

Calling:

```http
POST /tracking/{delivery_id}/events
```

can update the related Delivery.

For example:

```json
{
  "status": "in_transit",
  "location": "Kolkata",
  "latitude": 22.5726,
  "longitude": 88.3639
}
```

results conceptually in:

```text
TrackingEvent created
        +
Delivery.status = in_transit
Delivery.current_location = Kolkata
Delivery.current_latitude = 22.5726
Delivery.current_longitude = 88.3639
Delivery.last_gps_update = updated
```

Therefore another service does not need to separately update the Delivery location after submitting a TrackingEvent through this endpoint.

---

# Successful Response

**HTTP 201**

Returns the created TrackingEvent.

Example structure:

```json
{
  "id": 15,
  "delivery_id": 2,
  "status": "in_transit",
  "location": "Kolkata",
  "latitude": 22.5726,
  "longitude": 88.3639,
  "event_time": "2026-08-25T00:00:00",
  "description": "Shipment reached Kolkata"
}
```

---

# Get Tracking History

## `GET /tracking/{delivery_id}/events`

Returns all TrackingEvents associated with a Delivery.

### Path Parameter

| Parameter     | Type    | Required |
| ------------- | ------- | -------: |
| `delivery_id` | integer |      Yes |

### Example Request

```http
GET /tracking/2/events
```

---

# Event Ordering

TrackingEvents are returned in:

```text
event_time ASC
```

order.

This means the oldest event appears first and the newest event appears last.

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
Arrived
```

This makes the endpoint suitable for rendering a chronological shipment timeline.

---

# Example Response

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

# Get Active Shipments

## `GET /tracking/active`

Returns Deliveries whose current status is considered operationally active.

The current active statuses are:

```text
scheduled
in_transit
delayed
arrived
unloading
```

Conceptually:

```text
All Deliveries
      ↓
Filter by active statuses
      ↓
Return active shipments
```

Statuses such as:

```text
delivered
cancelled
```

are therefore not part of the active-shipment result.

---

# Tracking vs GPS Simulation

Tracking and Simulation work together, but they are not the same module.

### Tracking

Stores and retrieves shipment state/history.

### Simulation

Generates artificial GPS movement for testing/demo purposes.

```text
Simulation
    ↓
GPS Movement
    ↓
Delivery Location
    ↓
Tracking / Live UI
```

Simulation is documented separately in:

`simulation-api.md`

---

# Important Background Simulation Behavior

After GPS simulation is started, the background tracking loop can automatically update the Delivery's current GPS information.

However, the automatic background movement does **not create a new TrackingEvent for every GPS movement**.

Therefore:

```text
Delivery
    ↓
Latest current GPS position
```

and:

```text
TrackingEvents
    ↓
Historical event timeline
```

should not be treated as identical data streams.

---

# Manual Simulation Step

The endpoint:

```http
POST /simulation/step/{delivery_id}
```

does create a TrackingEvent while moving the simulated shipment.

Therefore manual simulation steps can appear in:

```http
GET /tracking/{delivery_id}/events
```

while every automatic background GPS movement may not.

---

# Live Map Integration

For a live map, the frontend should primarily use the Delivery's current coordinates.

For example:

```text
current_latitude
current_longitude
current_location
```

The dashboard also provides:

```http
GET /dashboard/live-shipments
```

which is designed to expose current active shipment information.

A frontend can poll the live-shipment/current Delivery data while simulation is active.

---

# Shipment Timeline Integration

For a shipment history/timeline component:

```text
Shipment Detail Page
        ↓
GET /tracking/{delivery_id}/events
        ↓
Receive events
        ↓
Already ordered by event_time
        ↓
Render Timeline
```

Example UI:

```text
● Shipment Created

│

● Siliguri Highway
  In Transit

│

● Kolkata
  Shipment reached Kolkata

│

● Destination Yard
  Arrived
```

---

# Cross-Team Integration

A different service can interact with E2 tracking without knowing Python or FastAPI.

For example, an external tracking service can submit:

```http
POST /tracking/2/events
```

with:

```json
{
  "status": "in_transit",
  "location": "Kolkata",
  "latitude": 22.5726,
  "longitude": 88.3639,
  "event_time": "2026-08-25T00:00:00",
  "description": "GPS update received"
}
```

E2 then handles:

```text
Create TrackingEvent
        +
Update Delivery state
```

The other system only needs to follow the HTTP API contract.

---

# Relationship with Operations

Tracking information is also important for operational exception detection.

For example, the Operations module checks situations where an in-transit shipment has not received GPS information.

Conceptually:

```text
Delivery is in_transit
        +
No GPS update
        ↓
Exception Detection
        ↓
Shipment Exception
        ↓
Alert
```

See:

`operations-api.md`

for the exact operational checks.

---

# Error Handling

Frontend/integrating services should handle:

| HTTP Status | Meaning                             |
| ----------: | ----------------------------------- |
|       `200` | Successful shipment/event retrieval |
|       `201` | TrackingEvent created               |
|       `404` | Delivery/shipment not found         |
|       `422` | Request/path validation failed      |

FastAPI HTTP errors use:

```json
{
  "detail": "Error message"
}
```

---

# Current Limitations

The current Tracking API does not provide:

* WebSocket shipment streaming
* Socket.IO tracking events
* Server-Sent Events
* Real GPS provider integration
* Pagination for TrackingEvent history

Live movement currently relies on the simulated GPS system and HTTP retrieval/polling.

Most importantly, **do not use TrackingEvent history as a frame-by-frame live GPS feed**.

Use:

```text
Current Delivery / Dashboard Live Shipments
```

for the latest position, and:

```text
GET /tracking/{delivery_id}/events
```

for the historical timeline.
