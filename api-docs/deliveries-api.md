# Deliveries API

The Deliveries API manages physical shipment records created for Restock Orders.

A Delivery is the main logistics entity in E2. Once created, it is used by the **Tracking, GPS Simulation, Operations & Alerts, Dock Operations, and Dashboard** modules.

**Base path:** `/deliveries`

---

## Endpoints

| Method | Endpoint                                 | Purpose                                   |
| ------ | ---------------------------------------- | ----------------------------------------- |
| POST   | `/deliveries/`                           | Create a Delivery                         |
| GET    | `/deliveries/`                           | Get all Deliveries                        |
| GET    | `/deliveries/{delivery_id}`              | Get a Delivery by ID                      |
| GET    | `/deliveries/tracking/{tracking_number}` | Find a Delivery using its tracking number |
| PUT    | `/deliveries/{delivery_id}/status`       | Update Delivery status                    |

---

# Delivery Object

A Delivery represents one shipment associated with a Restock Order.

The Delivery model stores information used throughout the logistics workflow, including:

| Field                   | Type            | Purpose                                      |
| ----------------------- | --------------- | -------------------------------------------- |
| `id`                    | integer         | Database-generated Delivery ID               |
| `restock_order_id`      | integer         | Restock Order associated with the shipment   |
| `dock_id`               | integer / null  | Assigned Yard Dock                           |
| `tracking_number`       | string / null   | Shipment tracking number                     |
| `carrier`               | string / null   | Shipment carrier                             |
| `status`                | string          | Current Delivery status                      |
| `scheduled_arrival`     | datetime / null | Planned arrival time                         |
| `actual_arrival`        | datetime / null | Actual arrival time                          |
| `current_latitude`      | float / null    | Latest shipment latitude                     |
| `current_longitude`     | float / null    | Latest shipment longitude                    |
| `current_location`      | string / null   | Latest location description                  |
| `destination_latitude`  | float / null    | Destination latitude                         |
| `destination_longitude` | float / null    | Destination longitude                        |
| `estimated_arrival`     | datetime / null | Current estimated arrival                    |
| `eta_minutes`           | integer / null  | Estimated remaining travel time              |
| `average_speed_kmph`    | float / null    | Current/simulated average speed              |
| `distance_remaining_km` | float / null    | Remaining distance                           |
| `last_gps_update`       | datetime / null | Latest GPS update time                       |
| `simulation_active`     | boolean         | Whether GPS simulation is running            |
| `delay_detected`        | boolean         | Whether delay logic flagged the Delivery     |
| `exception_detected`    | boolean         | Whether exception logic flagged the Delivery |

Some fields may be `null` until tracking, simulation, dock assignment, or operational processing supplies them.

---

# Create Delivery

## `POST /deliveries/`

Creates a new shipment for an existing Restock Order.

### Request

**Content-Type:** `application/json`

A typical request contains values such as:

```json
{
  "restock_order_id": 1,
  "dock_id": null,
  "tracking_number": "TRK-10001",
  "carrier": "ABC Logistics",
  "status": "scheduled"
}
```

Additional Delivery fields supported by the Delivery creation schema can be supplied when available.

---

# Required Relationship

A Delivery must reference an existing Restock Order.

```text
Restock Order
      ↓
restock_order_id
      ↓
   Delivery
```

A dock is optional during Delivery creation.

This allows a shipment to exist before its final Yard Dock has been selected.

---

# Backend Validation

Before creating a Delivery, the backend performs the following checks:

```text
Receive Delivery request
        ↓
Check Restock Order
        ↓
Exists?
 No → HTTP 404
        ↓ Yes
dock_id supplied?
   │
   ├── Yes → Check Yard Dock
   │             ↓
   │          Missing → HTTP 404
   │
   └── No
        ↓
tracking_number supplied?
        ↓
Check for duplicate
        ↓
Duplicate?
 Yes → HTTP 400
        ↓ No
Create Delivery
        ↓
Commit
        ↓
Return Delivery
```

---

## Restock Order Not Found

**HTTP 404**

```json
{
  "detail": "Restock order not found"
}
```

---

## Yard Dock Not Found

If a `dock_id` is supplied but that dock does not exist:

**HTTP 404**

```json
{
  "detail": "Yard dock not found"
}
```

---

## Duplicate Tracking Number

If another Delivery already uses the supplied tracking number:

**HTTP 400**

```json
{
  "detail": "Tracking number already exists"
}
```

This allows other modules to safely identify a shipment using its tracking number.

---

# Successful Creation

**HTTP 201**

The API returns the newly created Delivery object.

Conceptually:

```json
{
  "id": 2,
  "restock_order_id": 1,
  "dock_id": null,
  "tracking_number": "TRK-10001",
  "carrier": "ABC Logistics",
  "status": "scheduled",
  "actual_arrival": null,
  "simulation_active": false,
  "delay_detected": false,
  "exception_detected": false
}
```

Fields that have not yet been populated may be `null`.

---

# Get All Deliveries

## `GET /deliveries/`

Returns all Delivery records.

### Request

No body is required.

### Example Usage

```http
GET /deliveries/
```

### Response

The response is an array of Delivery objects.

```json
[
  {
    "id": 1,
    "restock_order_id": 1,
    "tracking_number": "TRK-001",
    "carrier": "ABC Logistics",
    "status": "in_transit"
  },
  {
    "id": 2,
    "restock_order_id": 2,
    "tracking_number": "TRK-002",
    "carrier": "XYZ Transport",
    "status": "scheduled"
  }
]
```

The actual returned objects contain the Delivery fields defined by the response schema.

The current endpoint does not implement pagination, filtering, or search parameters.

---

# Get Delivery by ID

## `GET /deliveries/{delivery_id}`

Returns a Delivery using its internal database ID.

### Path Parameter

| Parameter     | Type    | Required | Description          |
| ------------- | ------- | -------: | -------------------- |
| `delivery_id` | integer |      Yes | Delivery database ID |

Example:

```http
GET /deliveries/2
```

---

## Delivery Not Found

**HTTP 404**

```json
{
  "detail": "Delivery not found"
}
```

---

# Get Delivery by Tracking Number

## `GET /deliveries/tracking/{tracking_number}`

Finds a shipment using its external tracking number instead of the internal Delivery ID.

### Path Parameter

| Parameter         | Type   | Required | Description              |
| ----------------- | ------ | -------: | ------------------------ |
| `tracking_number` | string |      Yes | Shipment tracking number |

Example:

```http
GET /deliveries/tracking/TRK-10001
```

This endpoint is useful when another system knows the tracking number but does not know E2's internal `delivery_id`.

---

## Shipment Not Found

If no Delivery has the supplied tracking number, the API returns `404`.

---

# Update Delivery Status

## `PUT /deliveries/{delivery_id}/status`

Updates the operational status of a Delivery.

The new status is supplied as a **query parameter**.

### Path Parameter

| Parameter     | Type    | Required |
| ------------- | ------- | -------: |
| `delivery_id` | integer |      Yes |

### Query Parameter

| Parameter | Type   | Required |
| --------- | ------ | -------: |
| `status`  | string |      Yes |

Example:

```http
PUT /deliveries/2/status?status=arrived
```

---

# Supported Delivery Status Values

The current API accepts:

```text
scheduled
in_transit
delayed
arrived
unloading
delivered
cancelled
```

The supplied value is normalized before validation.

A normal business flow can be represented as:

```text
scheduled
    ↓
in_transit
    ↓
arrived
    ↓
unloading
    ↓
delivered
```

Additional operational states are:

```text
delayed

cancelled
```

---

# Invalid Status

If the supplied status is not in the allowed set, the API returns:

**HTTP 400**

with a FastAPI `detail` response describing the allowed status values.

---

# Arrival Side Effect

Updating a Delivery to:

```text
arrived
```

or:

```text
delivered
```

has an additional side effect.

If `actual_arrival` has not already been recorded, the backend sets:

```text
actual_arrival = current UTC time
```

Therefore another service does not need to separately submit an actual-arrival timestamp when using this status update route.

---

# Important Status Behavior

The backend validates **which status names are allowed**, but it does not currently enforce a strict transition state machine.

For example, the API itself does not enforce:

```text
scheduled
    ↓
in_transit
    ↓
arrived
    ↓
unloading
    ↓
delivered
```

as the only possible sequence.

Integrating clients should therefore use the agreed business sequence even though the current API does not strictly enforce every transition.

---

# How Delivery Connects to Other Modules

Delivery is the central logistics object.

```text
Restock Order
      ↓
   Delivery
      │
      ├────────→ Tracking
      │
      ├────────→ GPS Simulation
      │
      ├────────→ Operations
      │             ↓
      │           Alerts
      │
      ├────────→ Dock Operations
      │
      └────────→ Dashboard
```

Most logistics APIs use:

```text
delivery_id
```

as their reference.

Therefore, after creating a Delivery, the integrating application should keep the returned `id`.

---

# Tracking Integration

A Delivery can be retrieved using either:

```http
GET /deliveries/{delivery_id}
```

or its tracking number:

```http
GET /deliveries/tracking/{tracking_number}
```

The dedicated Tracking API additionally provides:

```http
GET /tracking/shipment/{tracking_number}
```

and:

```http
GET /tracking/{delivery_id}/events
```

The Delivery contains the latest shipment state, while TrackingEvents provide shipment history.

---

# GPS Simulation Integration

A Delivery can be placed into simulated movement using:

```http
POST /simulation/start/{delivery_id}
```

After simulation starts, the Delivery is updated with GPS/ETA information by the simulation/background logic.

Fields affected include:

```text
current_latitude
current_longitude
current_location
last_gps_update
distance_remaining_km
average_speed_kmph
eta_minutes
estimated_arrival
status
```

The latest Delivery state therefore acts as the source for current shipment position.

---

# ETA Integration

There are two ETA concepts in the project.

### Delivery/Simulation ETA

GPS simulation calculates ETA from the shipment's remaining distance and speed and stores the result on the Delivery.

### ML ETA

The separate:

```http
GET /eta/predict
```

endpoint uses the trained ML model.

These are separate mechanisms in the current implementation.

---

# Operations & Alerts Integration

The Operations module examines Delivery records for operational problems.

For example:

```http
POST /operations/detect-delays
```

can mark:

```text
delay_detected = true
status = delayed
```

and create an Alert.

Similarly:

```http
POST /operations/detect-exceptions
```

can set:

```text
exception_detected = true
```

when configured exception conditions are found.

---

# Dock Integration

A Delivery may initially have:

```text
dock_id = null
```

A dock can later be recommended using:

```http
GET /dock-operations/recommend/{delivery_id}
```

and assigned using:

```http
POST /dock-operations/assign/{delivery_id}
```

After assignment:

```text
Delivery.dock_id
      ↓
Selected YardDock
```

---

# Frontend Integration

A shipment list can use:

```text
Page Load
   ↓
GET /deliveries/
   ↓
Render shipment rows
```

A shipment detail screen can use:

```text
GET /deliveries/{delivery_id}
          │
          ├── shipment information
          │
          ├── current GPS
          │
          ├── ETA
          │
          ├── status
          │
          └── assigned dock
```

Then load related data:

```text
GET /tracking/{delivery_id}/events
          ↓
Shipment Timeline

GET /dock-operations/recommend/{delivery_id}
          ↓
Dock Recommendations

GET /operations/alerts
          ↓
Operational Alerts
```

---

# Cross-Team Integration Notes

For other backend/services, the most important identifier is:

```text
delivery_id
```

The tracking number can be used for external shipment lookup, but most internal E2 operational APIs use the Delivery ID.

Recommended integration pattern:

```text
POST /deliveries/
       ↓
Receive Delivery
       ↓
Store returned delivery.id
       ↓
Use ID for:
   tracking
   simulation
   dock operations
   operational workflows
```

---

# Error Handling

| HTTP Status | Meaning                                         |
| ----------: | ----------------------------------------------- |
|       `200` | Successful read/status update                   |
|       `201` | Delivery created                                |
|       `400` | Invalid status or duplicate tracking number     |
|       `404` | Delivery, Restock Order, or Yard Dock not found |
|       `422` | Request/path/query validation failure           |

FastAPI HTTP errors normally use:

```json
{
  "detail": "Error message"
}
```

---

# Current Limitations

The current Deliveries API does not implement:

* Pagination
* Search/filtering
* Strict status-transition enforcement
* Authentication/authorization
* Real GPS provider integration
* Automatic Delivery creation when a Restock Order is created

Creating a Restock Order does **not** automatically create a Delivery.

The expected integration remains:

```text
Create Restock Order
        ↓
POST /deliveries/
        ↓
Delivery created
        ↓
Tracking / Simulation / Operations / Dock workflow
```
