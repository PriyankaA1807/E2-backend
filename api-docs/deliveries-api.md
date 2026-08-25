# Deliveries API

The Deliveries API manages physical shipment records created for Restock Orders.

A Delivery is the central logistics entity in E2. Once created, it is used by:

- Tracking
- GPS Simulation
- ETA Prediction
- Operations & Alerts
- Yard Operations
- Dock Operations
- Dashboard
- PR2 Integration

**Base path:** `/deliveries`

---

# Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/deliveries/` | Create a Delivery |
| GET | `/deliveries/` | Get all Deliveries |
| GET | `/deliveries/{delivery_id}` | Get a Delivery by ID |
| GET | `/deliveries/tracking/{tracking_number}` | Find a Delivery by tracking number |
| PUT | `/deliveries/{delivery_id}/status` | Update Delivery lifecycle status |

---

# Delivery Object

A Delivery represents one physical shipment associated with a Restock Order.

The Delivery model stores:

| Field | Type | Purpose |
|---|---|---|
| `id` | integer | Internal E2 Delivery ID |
| `restock_order_id` | integer | Linked Restock Order |
| `dock_id` | integer / null | Assigned Yard Dock |
| `tracking_number` | string / null | Carrier tracking number |
| `trailer_id` | string / null | Trailer / vehicle identifier |
| `shipment_reference` | string / null | External shipment reference |
| `carrier` | string / null | Shipment carrier |
| `status` | string | Current lifecycle status |
| `scheduled_arrival` | datetime / null | Planned arrival |
| `actual_arrival` | datetime / null | Actual arrival |
| `current_latitude` | float / null | Current GPS latitude |
| `current_longitude` | float / null | Current GPS longitude |
| `current_location` | string / null | Latest location |
| `destination_latitude` | float / null | Destination latitude |
| `destination_longitude` | float / null | Destination longitude |
| `estimated_arrival` | datetime / null | Current ETA timestamp |
| `eta_minutes` | float / null | Remaining ETA |
| `average_speed_kmph` | float / null | Current/simulated speed |
| `distance_remaining_km` | float / null | Remaining distance |
| `last_gps_update` | datetime / null | Last GPS update |
| `simulation_active` | boolean | Whether simulation is running |
| `delay_detected` | boolean | Delay flag |
| `exception_detected` | boolean | Exception flag |

Some fields remain `null` until tracking, simulation, ETA prediction, dock assignment, or yard processing supplies them.

---

# Shipment Identification

E2 supports multiple identifiers for the same Delivery:

```text
tracking_number
trailer_id
shipment_reference
delivery_id
```

Conceptually:

```text
Tracking Number
Trailer ID
Shipment Reference
       ↓
    Delivery
       ↓
Internal E2 ID
```

Use:

- `tracking_number` for carrier/logistics lookup;
- `trailer_id` for yard/trailer operations;
- `shipment_reference` for cross-system correlation;
- `delivery_id` for internal E2 operational APIs.

---

# 1. Create Delivery

## Endpoint

```http
POST /deliveries/
```

Creates a new shipment for an existing Restock Order.

---

# Request Body

Example:

```json
{
  "restock_order_id": 1,
  "dock_id": null,
  "tracking_number": "TRK-E2-101",
  "trailer_id": "TRL-101",
  "shipment_reference": "SHIP-E2-101",
  "carrier": "BlueDart",
  "status": "scheduled",
  "scheduled_arrival": "2026-08-25T15:00:00",
  "destination_latitude": 23.0225,
  "destination_longitude": 72.5714
}
```

Additional Delivery fields may be supplied if supported by the schema.

---

# Required Relationship

A Delivery must reference an existing Restock Order:

```text
Restock Order
      ↓
restock_order_id
      ↓
Delivery
```

A dock is optional when the shipment is created.

This allows:

```text
Shipment Created
      ↓
No Dock Yet
      ↓
Later Recommendation / Scheduling / Assignment
```

---

# Backend Validation

The backend validates:

```text
Receive Delivery Request
        ↓
Restock Order Exists?
   No → 404
        ↓ Yes
dock_id supplied?
   ├── Yes → Validate Yard Dock
   └── No
        ↓
tracking_number supplied?
        ↓
Check duplicate
        ↓
Duplicate?
   Yes → 400
        ↓ No
Create Delivery
        ↓
Commit
        ↓
Return Delivery
```

---

# Restock Order Not Found

```http
404 Not Found
```

Example:

```json
{
  "detail": "Restock order not found"
}
```

---

# Yard Dock Not Found

If a supplied `dock_id` does not exist:

```http
404 Not Found
```

Example:

```json
{
  "detail": "Yard dock not found"
}
```

---

# Duplicate Tracking Number

If another Delivery already uses the same tracking number:

```http
400 Bad Request
```

Example:

```json
{
  "detail": "Tracking number already exists"
}
```

Tracking numbers should therefore be treated as unique shipment identifiers inside E2.

---

# Successful Creation

```http
201 Created
```

Example:

```json
{
  "restock_order_id": 1,
  "dock_id": null,
  "tracking_number": "TRK-E2-101",
  "trailer_id": "TRL-101",
  "shipment_reference": "SHIP-E2-101",
  "carrier": "BlueDart",
  "status": "scheduled",
  "scheduled_arrival": "2026-08-25T15:00:00",
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
  "id": 3,
  "delay_detected": false,
  "exception_detected": false,
  "last_gps_update": null
}
```

---

# 2. Get All Deliveries

## Endpoint

```http
GET /deliveries/
```

Returns all Delivery records.

---

# Example Request

```http
GET /deliveries/
```

---

# Example Response

```json
[
  {
    "restock_order_id": 1,
    "dock_id": 2,
    "tracking_number": "TRK-E2-101",
    "trailer_id": "TRL-101",
    "shipment_reference": "SHIP-E2-101",
    "carrier": "BlueDart",
    "status": "arrived_at_gate",
    "id": 3,
    "delay_detected": false,
    "exception_detected": false
  },
  {
    "restock_order_id": 3,
    "dock_id": null,
    "tracking_number": "TRK-PR2-TEST-001",
    "trailer_id": "TRL-PR2-001",
    "shipment_reference": "SHIP-PR2-001",
    "carrier": "BlueDart",
    "status": "scheduled",
    "id": 4,
    "delay_detected": false,
    "exception_detected": false
  }
]
```

The actual endpoint returns the complete Delivery response schema.

---

# 3. Get Delivery by ID

## Endpoint

```http
GET /deliveries/{delivery_id}
```

Returns a Delivery using the internal E2 ID.

---

# Path Parameter

| Parameter | Type | Required | Description |
|---|---|---:|---|
| `delivery_id` | integer | Yes | Internal E2 Delivery ID |

---

# Example Request

```http
GET /deliveries/4
```

---

# Delivery Not Found

```http
404 Not Found
```

Example:

```json
{
  "detail": "Delivery not found"
}
```

---

# 4. Get Delivery by Tracking Number

## Endpoint

```http
GET /deliveries/tracking/{tracking_number}
```

Finds a Delivery by tracking number.

---

# Path Parameter

| Parameter | Type | Required |
|---|---|---:|
| `tracking_number` | string | Yes |

---

# Example

```http
GET /deliveries/tracking/TRK-PR2-TEST-001
```

This is useful when another system knows the external tracking number but not E2's `delivery_id`.

For richer shipment lookup, the dedicated Tracking API also supports:

```http
GET /tracking/shipment/{tracking_number}
GET /tracking/trailer/{trailer_id}
GET /tracking/reference/{shipment_reference}
```

---

# 5. Update Delivery Status

## Endpoint

```http
PUT /deliveries/{delivery_id}/status
```

Updates the operational lifecycle state of a Delivery.

The new status is sent as a query parameter.

---

# Path Parameter

| Parameter | Type | Required |
|---|---|---:|
| `delivery_id` | integer | Yes |

---

# Query Parameter

| Parameter | Type | Required |
|---|---|---:|
| `status` | string | Yes |

---

# Example

```http
PUT /deliveries/3/status?status=in_yard
```

---

# Delivery Lifecycle

The current E2 lifecycle is designed around both transport and yard/dock operations.

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
completed
   ↓
departed
```

Delay can occur during the flow:

```text
in_transit
   ↓
delayed
```

Legacy test records may still contain:

```text
arrived
delivered
```

for compatibility with earlier data.

---

# Supported Operational States

Current lifecycle values can include:

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
completed
departed
cancelled
```

Legacy compatibility may also include:

```text
arrived
delivered
```

depending on existing records and implementation history.

---

# Lifecycle Validation

Unlike the older implementation, E2 now validates allowed state transitions.

Conceptually:

```text
Current Status
      ↓
Requested New Status
      ↓
Is Transition Allowed?
   ┌──────┴──────┐
   No            Yes
    ↓             ↓
  400        Apply Change
```

Example valid transition:

```text
arrived_at_gate
      ↓
in_yard
```

Example invalid transition:

```text
arrived_at_gate
      ↓
completed
```

If the transition is not permitted, the API rejects it.

---

# Why Lifecycle Validation Matters

A strict lifecycle prevents states such as:

```text
scheduled → unloading
```

or:

```text
arrived_at_gate → completed
```

from bypassing required yard/dock operations.

This protects downstream logic for:

- yard dashboards;
- dock scheduling;
- reassignment;
- operational alerts;
- trailer-door allocation.

---

# Arrival Side Effects

When a Delivery reaches an arrival-related state, E2 can set:

```text
actual_arrival
```

if it is not already populated.

For example:

```text
arrived_at_gate
```

can represent the physical arrival at the facility.

This timestamp is then used by yard and scheduling logic.

---

# Status and Yard State

Delivery status directly affects:

```text
/dashboard/yard-status
```

Examples:

```text
arrived_at_gate
      ↓
AT_GATE

in_yard
      ↓
IN_YARD

waiting_for_dock
      ↓
WAITING_FOR_DOCK

dock_assigned
      ↓
DOCK_ASSIGNED

docked
      ↓
DOCKED
```

---

# How Delivery Connects to Other Modules

Delivery is the central logistics object.

```text
Restock Order
      ↓
Delivery
   │
   ├── Tracking
   ├── GPS Simulation
   ├── ETA Prediction
   ├── Operations
   │      ↓
   │    Alerts
   │
   ├── Yard Status
   ├── Dock Scheduling
   ├── Dock Assignment
   ├── Dock Reassignment
   └── Dashboard
```

Most E2 operational APIs use:

```text
delivery_id
```

as their primary internal reference.

---

# Tracking Integration

A Delivery can be found using:

```http
GET /deliveries/{delivery_id}
```

or:

```http
GET /deliveries/tracking/{tracking_number}
```

The Tracking API provides additional lookup options:

```http
GET /tracking/shipment/{tracking_number}
GET /tracking/shipment/id/{delivery_id}
GET /tracking/trailer/{trailer_id}
GET /tracking/reference/{shipment_reference}
```

Tracking history is available through:

```http
GET /tracking/{delivery_id}/events
```

---

# GPS Simulation Integration

A Delivery can enter simulated movement using:

```http
POST /simulation/start/{delivery_id}
```

Simulation updates fields such as:

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

Manual simulation advancement:

```http
POST /simulation/step/{delivery_id}
```

Stop simulation:

```http
POST /simulation/stop/{delivery_id}
```

---

# ETA Integration

E2 currently supports:

```http
GET /eta/predict
```

for direct model prediction.

For an existing Delivery:

```http
POST /eta/predict-delivery/{delivery_id}
```

can use:

```text
Delivery.distance_remaining_km
RestockOrder.quantity
Supplier Delay History
Carrier Delay History
```

to calculate:

```text
Estimated Delivery Hours
Estimated Delivery Minutes
Estimated Arrival
Predicted Delay
```

The endpoint can also update:

```text
Delivery.estimated_arrival
Delivery.eta_minutes
Delivery.delay_detected
Delivery.status
```

and create/reuse a delay alert.

---

# Operations & Alerts Integration

Operations can evaluate the Delivery using:

```http
POST /operations/detect-delays
POST /operations/detect-exceptions
POST /operations/detect-dock-unavailable
POST /operations/detect-reassignment-required
```

Potential Delivery effects include:

```text
delay_detected = true
exception_detected = true
status = delayed
```

---

# Dock Integration

A Delivery can initially have:

```text
dock_id = null
```

Then E2 can:

```http
GET /dock-operations/recommend/{delivery_id}
```

generate a schedule through:

```http
GET /dock-operations/schedule
```

assign:

```http
POST /dock-operations/assign/{delivery_id}
```

reassign manually:

```http
POST /dock-operations/reassign/{delivery_id}
```

or automatically:

```http
POST /dock-operations/auto-reassign/{delivery_id}
```

---

# Dock Assignment Side Effect

After assignment:

```text
Delivery.dock_id
      ↓
Selected YardDock
```

and the selected Dock becomes:

```text
reserved
```

If a blocked current dock is replaced, the blocked status should remain blocked rather than being incorrectly restored to available.

---

# Dashboard Integration

Delivery data feeds:

```http
GET /dashboard/summary
GET /dashboard/live-shipments
GET /dashboard/yard-status
GET /dashboard/dock-schedule
GET /dashboard/trailer-door-allocation
GET /dashboard/insights
```

For example:

```text
Delivery
   ↓
Status + ETA + Dock + Flags
   ↓
Dashboard
```

---

# PR2 Integration

External systems such as PR2 can create E2 shipment records using:

```http
POST /integrations/shipments
```

PR2 sends information such as:

```text
external_order_id
tracking_number
trailer_id
shipment_reference
carrier
quantity
scheduled_arrival
destination
```

E2 then creates:

```text
ShipmentIntegration
+
RestockOrder
+
Delivery
```

The resulting Delivery can use all normal E2 workflows.

---

# Example PR2-Created Delivery

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
  "destination_latitude": 23.0225,
  "destination_longitude": 72.5714,
  "average_speed_kmph": 50,
  "simulation_active": false,
  "id": 4,
  "delay_detected": false,
  "exception_detected": false
}
```

---

# Frontend Integration

## Shipment List

```text
Page Load
   ↓
GET /deliveries/
   ↓
Render Shipment Rows
```

---

## Shipment Detail

```text
GET /deliveries/{delivery_id}
       │
       ├── Shipment Identity
       ├── GPS
       ├── ETA
       ├── Lifecycle State
       ├── Delay / Exception Flags
       └── Assigned Dock
```

Then load related data:

```text
GET /tracking/{delivery_id}/events
        ↓
Timeline

POST /eta/predict-delivery/{delivery_id}
        ↓
ML ETA

GET /dock-operations/recommend/{delivery_id}
        ↓
Dock Recommendations

GET /operations/alerts
        ↓
Operational Alerts
```

---

# Cross-Team Integration Notes

For external services, the best correlation identifiers are:

```text
tracking_number
trailer_id
shipment_reference
```

For internal E2 operational calls, use:

```text
delivery_id
```

Recommended pattern:

```text
External System
      ↓
Create / Import Shipment
      ↓
Receive delivery_id
      ↓
Use delivery_id for:
   tracking events
   simulation
   ETA
   dock operations
   operational workflows
```

---

# Error Handling

| HTTP Status | Meaning |
|---:|---|
| `200` | Successful read/status update |
| `201` | Delivery created |
| `400` | Invalid lifecycle transition / status / duplicate tracking number |
| `404` | Delivery, Restock Order, or Yard Dock not found |
| `422` | Request/path/query validation error |
| `500` | Unexpected backend/database error |

FastAPI errors generally use:

```json
{
  "detail": "Error message"
}
```

---

# Current Limitations

The current Deliveries API does not yet provide:

- pagination;
- advanced search/filtering;
- authentication/authorization;
- bulk delivery creation;
- real carrier API integration;
- automated shipment creation from every Restock Order;
- audit-history table for every lifecycle transition.

However, external shipment creation is supported through:

```http
POST /integrations/shipments
```

and lifecycle validation now protects yard/dock workflow consistency.

---

# Summary

The Delivery is the central operational entity in E2.

```text
Restock Order / External Shipment
           ↓
        Delivery
           │
           ├── Tracking
           ├── GPS
           ├── ETA
           ├── Operations
           ├── Yard
           ├── Dock Scheduling
           ├── Reassignment
           └── Dashboard
```

All major logistics workflows ultimately connect back to the Delivery record.
