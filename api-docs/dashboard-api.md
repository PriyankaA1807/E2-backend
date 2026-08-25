# Dashboard API

The Dashboard API provides aggregated operational data for the E2 frontend.

It combines shipment, yard, dock, inventory, alert, ETA, and scheduling information into frontend-ready responses.

**Base path:** `/dashboard`

---

# Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/dashboard/summary` | Get overall operational KPIs |
| GET | `/dashboard/live-shipments` | Get active shipment information |
| GET | `/dashboard/dock-status` | Get current Yard Dock status |
| GET | `/dashboard/yard-status` | Get current operational trailer/yard state |
| GET | `/dashboard/dock-schedule` | Get current dock schedule and arrival windows |
| GET | `/dashboard/trailer-door-allocation` | Get current vs recommended trailer-door allocation |
| GET | `/dashboard/insights` | Get rule-based operational insights |

---

# 1. Dashboard Summary

## Endpoint

```http
GET /dashboard/summary
```

Returns the main operational statistics required by the dashboard.

No request body or query parameters are required.

---

## Example Request

```http
GET /dashboard/summary
```

---

## Example Response

```json
{
  "shipments": {
    "total": 10,
    "active": 5,
    "completed": 3,
    "delayed": 2,
    "exceptions": 1
  },
  "docks": {
    "total": 6,
    "available": 2,
    "occupied": 1,
    "reserved": 1,
    "blocked": 1,
    "maintenance": 1
  },
  "inventory": {
    "low_stock_items": 3,
    "pending_restock_orders": 2
  },
  "alerts": {
    "active": 2
  }
}
```

The values above are examples.

Actual values are calculated from the current database state.

---

# Shipment Calculations

## Total

Counts all Delivery records.

---

## Active

A Delivery is considered active when its status belongs to the active operational lifecycle.

Current active statuses include:

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
arrived
```

`arrived` is retained for legacy compatibility with older test data.

---

## Completed

Completed/inactive shipment states can include:

```text
completed
departed
delivered
```

depending on lifecycle compatibility and historical records.

---

## Delayed

Counts Deliveries where:

```text
delay_detected == true
```

---

## Exceptions

Counts Deliveries where:

```text
exception_detected == true
```

---

# Dock Calculations

The dashboard summary exposes:

```text
total
available
occupied
reserved
blocked
maintenance
```

`total` counts all YardDock records.

The remaining fields count docks by their current operational state.

---

# Inventory Calculations

## Low Stock

An Inventory item is considered low stock when:

```text
inventory.current_stock <= product.reorder_level
```

---

## Pending Restock Orders

Counts RestockOrders where:

```text
status == pending
```

---

# Active Alerts

Counts Alerts where:

```text
resolved == false
```

---

# 2. Live Shipments

## Endpoint

```http
GET /dashboard/live-shipments
```

Returns Deliveries currently considered operationally active.

---

## Example Request

```http
GET /dashboard/live-shipments
```

---

# Response Fields

| Field | Type | Description |
|---|---|---|
| `id` | integer | Delivery ID |
| `tracking_number` | string / null | Shipment tracking number |
| `trailer_id` | string / null | Trailer identifier |
| `shipment_reference` | string / null | Shipment reference |
| `carrier` | string / null | Carrier |
| `status` | string | Delivery status |
| `latitude` | float / null | Current latitude |
| `longitude` | float / null | Current longitude |
| `location` | string / null | Current location |
| `eta_minutes` | float / null | Remaining ETA |
| `scheduled_arrival` | datetime / null | Scheduled arrival |
| `estimated_arrival` | datetime / null | Estimated arrival |
| `dock_id` | integer / null | Current dock |
| `delay_detected` | boolean | Delay flag |
| `exception_detected` | boolean | Exception flag |

---

## Example Response

```json
[
  {
    "id": 2,
    "tracking_number": "TR-2045",
    "trailer_id": null,
    "shipment_reference": null,
    "carrier": "BlueDart",
    "status": "delayed",
    "latitude": 22.617127619508526,
    "longitude": 86.8240995254175,
    "location": "22.61713, 86.82410",
    "eta_minutes": 1768.39,
    "scheduled_arrival": "2026-08-24T12:00:00",
    "estimated_arrival": "2026-08-26T19:22:18.668918",
    "dock_id": 1,
    "delay_detected": true,
    "exception_detected": true
  }
]
```

---

# Frontend Usage

This endpoint can drive:

- live shipment maps;
- active shipment tables;
- shipment status badges;
- ETA displays;
- delay indicators;
- exception indicators.

Because the backend currently uses HTTP rather than WebSockets, the frontend can poll this endpoint periodically.

Coordinates can be `null`, so map components should validate latitude/longitude before rendering a marker.

---

# 3. Dock Status

## Endpoint

```http
GET /dashboard/dock-status
```

Returns the current state and capabilities of all Yard Docks.

---

## Response Fields

| Field | Type | Description |
|---|---|---|
| `id` | integer | Dock ID |
| `yard_name` | string | Yard name |
| `dock_number` | string | Dock number |
| `status` | string | Current operational state |
| `dock_type` | string | Dock type |
| `supported_vehicle_type` | string | Supported vehicle type |
| `max_vehicle_length` | float | Maximum supported vehicle length |
| `refrigerated` | boolean | Refrigeration support |
| `hazardous_allowed` | boolean | Hazardous-load support |

---

## Example Response

```json
[
  {
    "id": 1,
    "yard_name": "Main Warehouse",
    "dock_number": "D-01",
    "status": "blocked",
    "dock_type": "standard",
    "supported_vehicle_type": "truck",
    "max_vehicle_length": 20,
    "refrigerated": false,
    "hazardous_allowed": false
  },
  {
    "id": 2,
    "yard_name": "Kolkata Main Yard",
    "dock_number": "D-01",
    "status": "reserved",
    "dock_type": "standard",
    "supported_vehicle_type": "truck",
    "max_vehicle_length": 20,
    "refrigerated": false,
    "hazardous_allowed": false
  }
]
```

---

# Frontend Usage

This endpoint can power a dock-status board.

```text
GET /dashboard/dock-status
        ↓
Dock Cards
        ↓
Available
Reserved
Occupied
Blocked
Maintenance
```

For changing dock status, use:

```http
PUT /yard-docks/{dock_id}
```

For assignment/reassignment, use the Dock Operations API.

---

# 4. Yard Status

## Endpoint

```http
GET /dashboard/yard-status
```

Returns a consolidated operational view of active trailers and their current yard state.

This endpoint is designed for yard-control and trailer-monitoring screens.

---

# Summary Fields

The response contains:

```text
total_active_trailers
at_gate
in_yard
waiting_for_dock
dock_assigned
docked_or_unloading
delayed
```

---

# Operational State Mapping

E2 maps Delivery statuses to frontend-friendly operational states.

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

unloading
      ↓
UNLOADING

delayed
      ↓
DELAYED_IN_TRANSIT

in_transit
      ↓
IN_TRANSIT

scheduled
      ↓
SCHEDULED
```

Legacy records with:

```text
arrived
```

can appear as:

```text
ARRIVED_LEGACY
```

---

# Example Yard Status Response

```json
{
  "summary": {
    "total_active_trailers": 3,
    "at_gate": 1,
    "in_yard": 0,
    "waiting_for_dock": 0,
    "dock_assigned": 0,
    "docked_or_unloading": 0,
    "delayed": 1
  },
  "trailers": [
    {
      "delivery_id": 3,
      "tracking_number": "TRK-E2-101",
      "trailer_id": "TRL-101",
      "shipment_reference": "SHIP-E2-101",
      "carrier": "BlueDart",
      "status": "arrived_at_gate",
      "operational_state": "AT_GATE",
      "yard_location": null,
      "current_latitude": null,
      "current_longitude": null,
      "scheduled_arrival": "2026-08-25T15:00:00",
      "estimated_arrival": null,
      "actual_arrival": "2026-08-25T12:59:24.029154",
      "eta_minutes": null,
      "distance_remaining_km": null,
      "delay_detected": false,
      "exception_detected": false,
      "assigned_dock": {
        "dock_id": 2,
        "yard_name": "Kolkata Main Yard",
        "dock_number": "D-01",
        "dock_status": "reserved",
        "dock_type": "standard"
      }
    }
  ]
}
```

---

# Trailer Fields

| Field | Description |
|---|---|
| `delivery_id` | E2 Delivery ID |
| `tracking_number` | Shipment tracking number |
| `trailer_id` | Trailer identifier |
| `shipment_reference` | Shipment reference |
| `carrier` | Carrier |
| `status` | Raw Delivery status |
| `operational_state` | Frontend-friendly yard state |
| `yard_location` | Latest known location |
| `current_latitude` | Current latitude |
| `current_longitude` | Current longitude |
| `scheduled_arrival` | Planned arrival |
| `estimated_arrival` | Predicted arrival |
| `actual_arrival` | Actual recorded arrival |
| `eta_minutes` | Remaining ETA |
| `distance_remaining_km` | Remaining distance |
| `delay_detected` | Delay flag |
| `exception_detected` | Exception flag |
| `assigned_dock` | Current dock information |

---

# Assigned Dock Object

Example:

```json
{
  "dock_id": 2,
  "yard_name": "Kolkata Main Yard",
  "dock_number": "D-01",
  "dock_status": "reserved",
  "dock_type": "standard"
}
```

If no dock exists:

```json
"assigned_dock": null
```

---

# Frontend Usage

```text
GET /dashboard/yard-status
       ↓
Yard Control Screen
       │
       ├── At Gate
       ├── In Yard
       ├── Waiting for Dock
       ├── Dock Assigned
       ├── Docked
       └── Delayed
```

This endpoint is more operationally detailed than `/dashboard/live-shipments`.

---

# 5. Dock Schedule

## Endpoint

```http
GET /dashboard/dock-schedule
```

Returns the centralized arrival-window dock schedule.

It reuses the same scheduler exposed through:

```http
GET /dock-operations/schedule
```

---

# Schedule Purpose

The schedule answers:

```text
Which trailer?
      ↓
Which dock?
      ↓
At what time?
```

Current slot duration:

```text
30 minutes
```

---

# Example Response

```json
{
  "generated_at": "2026-08-25T14:09:33.479125",
  "slot_duration_minutes": 30,
  "total_incoming_trailers": 3,
  "total_docks": 2,
  "scheduled_count": 3,
  "unscheduled_count": 0,
  "schedule": [
    {
      "delivery_id": 3,
      "tracking_number": "TRK-E2-101",
      "trailer_id": "TRL-101",
      "shipment_reference": "SHIP-E2-101",
      "delivery_status": "arrived_at_gate",
      "load_type": "standard",
      "priority_score": 2,
      "scheduled_arrival": "2026-08-25T15:00:00",
      "estimated_arrival": null,
      "effective_arrival": "2026-08-25T12:59:24.029154",
      "dock_id": 2,
      "yard_name": "Kolkata Main Yard",
      "dock_number": "D-01",
      "dock_type": "standard",
      "window_start": "2026-08-25T15:09:33.475116",
      "window_end": "2026-08-25T15:39:33.475116",
      "score": 100,
      "reasons": [
        "Existing dock assignment preserved"
      ]
    }
  ],
  "unscheduled": []
}
```

---

# Schedule Logic

The scheduler considers:

```text
Arrival Time
+
Dock Availability
+
Existing Assignment
+
Existing Time Slots
+
Compatibility
+
Waiting Time
+
Operational Priority
```

A blocked or maintenance dock should not be preserved as a valid scheduled dock.

---

# Example Reassignment Scheduling

```text
Delivery 2
Current Dock = 1
Dock 1 = blocked
       ↓
Do not preserve Dock 1
       ↓
Evaluate Dock 2
       ↓
Dock 2 scheduled
```

---

# Frontend Usage

This endpoint can power:

- dock calendars;
- trailer arrival timelines;
- door assignment boards;
- yard planning screens.

---

# 6. Trailer-Door Allocation

## Endpoint

```http
GET /dashboard/trailer-door-allocation
```

Provides a consolidated view of each active trailer's current dock and the dock selected by the latest schedule.

This endpoint is designed to answer:

```text
Is the current assignment still valid?
```

and:

```text
If not, where should the trailer go?
```

---

# Summary Fields

```text
total_trailers
currently_assigned
assignment_recommended
reassignment_required
unscheduled
delayed
```

---

# Example Response

```json
{
  "generated_at": "2026-08-25T14:12:56.320732",
  "summary": {
    "total_trailers": 3,
    "currently_assigned": 2,
    "assignment_recommended": 0,
    "reassignment_required": 1,
    "unscheduled": 0,
    "delayed": 1
  },
  "allocations": [
    {
      "delivery_id": 2,
      "tracking_number": "TR-2045",
      "trailer_id": null,
      "shipment_reference": null,
      "carrier": "BlueDart",
      "delivery_status": "delayed",
      "scheduled_arrival": "2026-08-24T12:00:00",
      "estimated_arrival": "2026-08-26T19:22:18.668918",
      "actual_arrival": null,
      "eta_minutes": 1768.39,
      "delay_detected": true,
      "exception_detected": true,
      "current_dock": {
        "dock_id": 1,
        "yard_name": "Main Warehouse",
        "dock_number": "D-01",
        "dock_status": "blocked",
        "dock_type": "standard"
      },
      "scheduled_dock": {
        "dock_id": 2,
        "yard_name": "Kolkata Main Yard",
        "dock_number": "D-01",
        "dock_type": "standard",
        "window_start": "2026-08-26T19:22:18.668918",
        "window_end": "2026-08-26T19:52:18.668918",
        "score": 85,
        "reasons": [
          "Vehicle type compatible",
          "Load type compatible",
          "Dock available after existing slot",
          "Minimal waiting time",
          "High operational priority"
        ]
      },
      "reassignment_required": true,
      "allocation_status": "REASSIGNMENT_RECOMMENDED"
    }
  ]
}
```

---

# Allocation Statuses

Important allocation states include:

```text
CURRENT_ASSIGNMENT_VALID
CURRENTLY_ASSIGNED
ASSIGNMENT_RECOMMENDED
REASSIGNMENT_RECOMMENDED
REASSIGNMENT_REQUIRED_NO_DOCK
UNSCHEDULED
```

---

# Current Assignment Valid

Example:

```text
Current Dock = 2
Scheduled Dock = 2
Current Dock usable
       ↓
CURRENT_ASSIGNMENT_VALID
```

---

# Assignment Recommended

Example:

```text
Delivery.dock_id = null
Scheduled Dock = 2
       ↓
ASSIGNMENT_RECOMMENDED
```

---

# Reassignment Recommended

Example:

```text
Current Dock = 1
Dock 1 = blocked

Scheduled Dock = 2
       ↓
REASSIGNMENT_RECOMMENDED
```

---

# Reassignment Required Without Alternative

Example:

```text
Current Dock = blocked
       ↓
No valid replacement dock
       ↓
REASSIGNMENT_REQUIRED_NO_DOCK
```

---

# Frontend Usage

This endpoint is useful for:

- trailer-to-door allocation boards;
- conflict indicators;
- reassignment banners;
- current-vs-recommended dock views;
- operations-control dashboards.

Example:

```text
TR-2045

Current:
Main Warehouse / D-01
BLOCKED

Recommended:
Kolkata Main Yard / D-01

Status:
REASSIGNMENT_RECOMMENDED
```

---

# Relationship with Dock Operations

If:

```text
allocation_status = REASSIGNMENT_RECOMMENDED
```

the frontend or another service can call:

```http
POST /dock-operations/auto-reassign/{delivery_id}
```

Then re-fetch:

```http
GET /dashboard/trailer-door-allocation
```

to verify the new assignment.

---

# 7. Operational Insights

## Endpoint

```http
GET /dashboard/insights
```

Returns human-readable operational insights calculated from current backend state.

These insights are rule-based.

They are not generated by the Random Forest ETA model.

---

# Delay Insight

If:

```text
Delivery.delay_detected == true
```

E2 can return:

```json
{
  "type": "delay",
  "priority": "high",
  "message": "1 shipment(s) are delayed. Review ETA and dock allocation."
}
```

---

# No Available Docks

If:

```text
available docks == 0
```

the backend generates a high-priority dock-capacity insight.

---

# Limited Dock Availability

If:

```text
available docks <= 2
```

but at least one is available, a medium-priority capacity insight can be returned.

---

# Blocked Dock Insight

If blocked docks exist, E2 can return an insight such as:

```json
{
  "type": "dock_blocked",
  "priority": "high",
  "message": "1 dock(s) are currently blocked."
}
```

---

# Maintenance Insight

If docks are under maintenance:

```json
{
  "type": "dock_maintenance",
  "priority": "medium",
  "message": "1 dock(s) are currently under maintenance."
}
```

---

# Unresolved Alerts

If unresolved Alerts exist:

```json
{
  "type": "alerts",
  "priority": "high",
  "message": "There are 2 unresolved operational alerts."
}
```

---

# Normal Operations

If no rule produces an operational issue:

```json
{
  "type": "system",
  "priority": "low",
  "message": "Operations are currently running normally."
}
```

---

# Dashboard Data Flow

```text
Deliveries
      │
      ├── Tracking
      ├── ETA
      ├── Delay
      └── Exceptions
      │
Yard Docks
      │
      ├── Availability
      ├── Reservations
      ├── Blocked State
      └── Maintenance
      │
Inventory
      │
Restock Orders
      │
Alerts
      │
      ▼
Dashboard API
      │
      ├── Summary
      ├── Live Shipments
      ├── Dock Status
      ├── Yard Status
      ├── Dock Schedule
      ├── Trailer-Door Allocation
      └── Insights
      │
      ▼
Frontend
```

---

# Recommended Frontend Integration

```text
GET /dashboard/summary
        ↓
KPI Cards

GET /dashboard/live-shipments
        ↓
Live Map / Active Shipment Table

GET /dashboard/dock-status
        ↓
Dock Status Board

GET /dashboard/yard-status
        ↓
Yard Control Board

GET /dashboard/dock-schedule
        ↓
Dock Schedule / Arrival Windows

GET /dashboard/trailer-door-allocation
        ↓
Trailer-to-Door Assignment Screen

GET /dashboard/insights
        ↓
Operational Insight Cards
```

The frontend should consume these calculated results instead of recreating backend aggregation or scheduling logic.

---

# Relationship with PR2 Integration

PR2 can create a shipment using:

```http
POST /integrations/shipments
```

After import, that shipment becomes a normal E2 Delivery.

It can then appear in:

```text
/dashboard/summary
/dashboard/live-shipments
/dashboard/yard-status
/dashboard/dock-schedule
/dashboard/trailer-door-allocation
```

Conceptually:

```text
PR2
  ↓
Integration API
  ↓
Delivery
  ↓
Dashboard
```

---

# Relationship with ETA

The ML delivery ETA endpoint can update:

```text
estimated_arrival
eta_minutes
delay_detected
```

These values then appear in Dashboard responses.

```text
ML ETA
   ↓
Delivery Updated
   ↓
Dashboard
```

---

# Relationship with Operations

Operations detects:

```text
Delay
Exception
Dock Unavailable
Reassignment Required
```

Dashboard endpoints expose the resulting Delivery, Dock, Alert, and scheduling state.

---

# Relationship with Tracking

Tracking and GPS update:

```text
current_latitude
current_longitude
current_location
last_gps_update
```

Dashboard endpoints expose the latest state for frontend monitoring.

---

# Error Handling

Empty data is considered a normal response.

For example:

```json
[]
```

can be returned when no active shipments exist.

Summary counters can validly be:

```json
0
```

The schedule can return:

```json
{
  "schedule": [],
  "unscheduled": []
}
```

depending on current data.

Unexpected database/backend failures can result in:

```http
500 Internal Server Error
```

---

# Current Limitations

The Dashboard API currently does not provide:

- historical time-series analytics;
- date-range filtering;
- yard-specific filtering;
- supplier-specific filtering;
- pagination;
- WebSocket/SSE streaming;
- authentication/authorization;
- persistent historical dock-schedule snapshots;
- advanced BI/reporting exports.

The current dashboard is focused on **current operational state**.

---

# Summary

The Dashboard API is the frontend-facing operational aggregation layer of E2.

```text
Tracking
+
ETA
+
Yard
+
Dock Scheduling
+
Operations
+
Alerts
        ↓
     Dashboard
        ↓
   Frontend UI
```

It provides both high-level KPIs and detailed operational views such as yard state, dock schedules, and trailer-door allocation.
