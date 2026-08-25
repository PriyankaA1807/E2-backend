# Dock Operations API

The Dock Operations API handles operational dock decisions for E2 Deliveries.

It supports:

- dock recommendation;
- arrival-window dock scheduling;
- manual dock assignment;
- manual dock reassignment;
- automatic dock reassignment.

**Base path:** `/dock-operations`

---

# Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/dock-operations/recommend/{delivery_id}` | Rank suitable docks for a Delivery |
| GET | `/dock-operations/schedule` | Generate dock schedule and arrival windows |
| POST | `/dock-operations/assign/{delivery_id}` | Assign a selected dock |
| POST | `/dock-operations/reassign/{delivery_id}` | Manually move a Delivery to another dock |
| POST | `/dock-operations/auto-reassign/{delivery_id}` | Automatically select and reserve a replacement dock |

---

# Overall Dock Workflow

```text
Delivery
   ↓
Dock Recommendation
   ↓
Dock Scheduling
   ↓
Assignment
   ↓
Operational Condition Changes?
   ├── No
   │    ↓
   │  Continue
   │
   └── Yes
        ↓
Current Dock Invalid?
        ↓
Reassignment
        ↓
New Dock Reserved
```

Recommendation, scheduling, and assignment are separate responsibilities.

---

# 1. Recommend Docks

## Endpoint

```http
GET /dock-operations/recommend/{delivery_id}
```

Returns ranked Yard Dock recommendations for an existing Delivery.

---

## Path Parameter

| Parameter | Type | Required | Description |
|---|---|---:|---|
| `delivery_id` | integer | Yes | Delivery requiring dock evaluation |

---

## Example Request

```http
GET /dock-operations/recommend/3
```

---

# Recommendation Flow

```text
Delivery ID
    ↓
Find Delivery
    ↓
Load Yard Docks
    ↓
Evaluate Each Dock
    ↓
Calculate Score
    ↓
Determine Compatibility
    ↓
Sort Highest Score First
    ↓
Return Recommendations
```

---

# Recommendation Scoring

The recommendation helper evaluates the current dock configuration.

## Dock Not Available

If:

```text
dock.status != available
```

the recommendation can return:

```text
score = 0
compatible = false
```

with a reason such as:

```text
Dock is not available
```

---

## Available Dock

An available dock receives:

```text
+50
```

---

## Truck-Compatible Dock

If:

```text
supported_vehicle_type == truck
```

the dock receives:

```text
+20
```

---

## Refrigerated Capability

If:

```text
refrigerated == true
```

the dock receives:

```text
+10
```

---

## Standard Dock

If:

```text
dock_type == standard
```

the dock receives:

```text
+10
```

---

## Delayed Shipment Priority

For the updated recommendation logic, a delayed Delivery can receive additional priority during scoring.

Conceptually:

```text
Delivery.delay_detected = true
        ↓
Additional operational priority
```

---

# Recommendation Response

Example structure:

```json
[
  {
    "dock_id": 2,
    "yard_name": "Kolkata Main Yard",
    "dock_number": "D-01",
    "score": 80,
    "compatible": true,
    "reasons": [
      "Dock is available",
      "Vehicle type compatible",
      "Standard dock suitable for shipment"
    ]
  },
  {
    "dock_id": 1,
    "yard_name": "Main Warehouse",
    "dock_number": "D-01",
    "score": 0,
    "compatible": false,
    "reasons": [
      "Dock is not available"
    ]
  }
]
```

The frontend should use the returned score and reasons rather than reproduce the algorithm.

---

# 2. Dock Schedule

## Endpoint

```http
GET /dock-operations/schedule
```

Generates an operational dock schedule for incoming active trailers.

The same scheduling engine is also exposed to the dashboard through:

```http
GET /dashboard/dock-schedule
```

---

# Schedule Purpose

Dock recommendation answers:

```text
Which dock is suitable?
```

Dock scheduling additionally answers:

```text
Which dock?
+
At what time?
```

The scheduler considers:

- effective arrival time;
- current dock assignment;
- dock availability;
- blocked/maintenance state;
- already scheduled time windows;
- shipment priority;
- waiting time;
- dock compatibility.

---

# Slot Duration

Current schedule slot duration:

```text
30 minutes
```

---

# Effective Arrival

The scheduler determines an effective arrival using available shipment timing information.

Conceptually:

```text
Actual Arrival
      ↓ if available
Estimated Arrival
      ↓ otherwise
Scheduled Arrival
      ↓ otherwise
No valid arrival time
```

A shipment without any usable arrival time may appear under:

```text
unscheduled
```

---

# Scheduling Priority

Priority can be influenced by operational state.

Conceptually:

```text
Delayed Shipment
      ↓
Higher Priority

Arrived at Gate
      ↓
Elevated Priority

Normal Scheduled Shipment
      ↓
Normal Priority
```

---

# Existing Assignment Handling

An existing dock assignment may be preserved only when the dock is operationally usable.

The scheduler does not preserve assignments to docks with statuses such as:

```text
blocked
maintenance
occupied
```

This prevents a blocked dock from continuing to appear as a valid scheduled destination.

---

# Example Blocked-Dock Behavior

Before correction:

```text
Delivery 2
    ↓
Dock 1
    ↓
blocked
    ↓
Existing assignment preserved
```

This was invalid.

Current behavior:

```text
Delivery 2
    ↓
Current Dock 1 = blocked
    ↓
Do not preserve
    ↓
Evaluate usable alternatives
    ↓
Dock 2 selected
```

---

# Schedule Example Response

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

# Schedule Response Fields

## Top-Level

| Field | Type | Description |
|---|---|---|
| `generated_at` | datetime | Schedule-generation time |
| `slot_duration_minutes` | integer | Duration of each dock slot |
| `total_incoming_trailers` | integer | Deliveries considered |
| `total_docks` | integer | Docks configured |
| `scheduled_count` | integer | Successfully scheduled deliveries |
| `unscheduled_count` | integer | Deliveries without a valid schedule |
| `schedule` | array | Scheduled trailer entries |
| `unscheduled` | array | Unscheduled trailers with reasons |

---

# Scheduled Item Fields

| Field | Description |
|---|---|
| `delivery_id` | E2 Delivery ID |
| `tracking_number` | Shipment tracking number |
| `trailer_id` | Trailer ID |
| `shipment_reference` | Shipment reference |
| `delivery_status` | Current Delivery status |
| `load_type` | Operational load type |
| `priority_score` | Scheduling priority |
| `scheduled_arrival` | Planned arrival |
| `estimated_arrival` | Predicted arrival |
| `effective_arrival` | Arrival time used by scheduler |
| `dock_id` | Selected dock |
| `yard_name` | Yard name |
| `dock_number` | Dock number |
| `dock_type` | Dock type |
| `window_start` | Scheduled slot start |
| `window_end` | Scheduled slot end |
| `score` | Scheduling score |
| `reasons` | Reasons supporting selection |

---

# Unscheduled Shipment

If no usable dock can be found, an entry can appear under:

```json
{
  "delivery_id": 5,
  "tracking_number": "TRK-005",
  "trailer_id": "TRL-005",
  "shipment_reference": "SHIP-005",
  "status": "waiting_for_dock",
  "reason": "No compatible usable dock found"
}
```

Other possible reasons include missing arrival information.

---

# 3. Assign Dock

## Endpoint

```http
POST /dock-operations/assign/{delivery_id}
```

Assigns a selected Yard Dock to a Delivery.

---

# Request Body

```json
{
  "dock_id": 2
}
```

---

# Assignment Validation

The backend validates:

```text
Delivery exists?
      ↓
Dock exists?
      ↓
Dock.status == available?
      ↓
Assign
```

Only an available dock can be manually assigned.

---

# Assignment Side Effects

```text
Delivery.dock_id
      ↓
Selected Dock

Selected Dock.status
      ↓
reserved
```

If the Delivery is currently:

```text
waiting_for_dock
```

the updated lifecycle can move it to:

```text
dock_assigned
```

---

# Old Dock Release Behavior

If the Delivery already has a previous dock reservation, the backend can release the previous reservation when moving to a new dock.

A blocked or maintenance state should not be overwritten simply because the Delivery changes assignment.

Conceptually:

```text
Old Dock = reserved
        ↓
Release to available

Old Dock = blocked
        ↓
Remain blocked
```

---

# 4. Manual Reassignment

## Endpoint

```http
POST /dock-operations/reassign/{delivery_id}
```

Moves the Delivery from its current dock to a specifically selected available dock.

---

# Request Body

```json
{
  "dock_id": 2
}
```

---

# Reassignment Validation

The backend checks:

```text
Delivery exists
      ↓
New Dock exists
      ↓
New Dock differs from current dock
      ↓
New Dock is available
      ↓
Reassign
```

---

# Reassignment Side Effects

```text
Old Reservation
      ↓
Released when appropriate

New Dock
      ↓
reserved

Delivery
      ↓
dock_id = new dock
```

If the Delivery is waiting for a dock, it can transition to:

```text
dock_assigned
```

---

# 5. Automatic Dock Reassignment

## Endpoint

```http
POST /dock-operations/auto-reassign/{delivery_id}
```

Automatically finds and reserves the best compatible available replacement dock.

The caller does not provide a `dock_id`.

---

# Example Request

```http
POST /dock-operations/auto-reassign/3
```

No request body is required.

---

# Automatic Reassignment Flow

```text
Delivery
   ↓
Find Current Dock
   ↓
Load Available Docks
   ↓
Ignore Current Dock
   ↓
Score Compatible Candidates
   ↓
Sort Highest Score First
   ↓
Select Best Dock
   ↓
Release Old Reservation if appropriate
   ↓
Reserve New Dock
   ↓
Update Delivery.dock_id
   ↓
Commit
```

---

# Example Successful Response

```json
{
  "restock_order_id": 1,
  "dock_id": 2,
  "tracking_number": "TRK-E2-101",
  "trailer_id": "TRL-101",
  "shipment_reference": "SHIP-E2-101",
  "carrier": "BlueDart",
  "status": "arrived_at_gate",
  "scheduled_arrival": "2026-08-25T15:00:00",
  "actual_arrival": "2026-08-25T12:59:24.029154",
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

# No Replacement Available

If there is no compatible available dock, the backend can return:

```http
409 Conflict
```

with a response similar to:

```json
{
  "detail": {
    "message": "No compatible available dock found for reassignment",
    "delivery_id": 3,
    "current_dock_id": 1
  }
}
```

---

# Relationship with Yard Docks

The Yard Docks API manages dock configuration and operational status:

```text
/yard-docks
```

Dock Operations uses that state:

```text
/dock-operations
```

Architecture:

```text
Yard Docks
    ↓
Dock Configuration
    ↓
Dock Operations
    ├── Recommend
    ├── Schedule
    ├── Assign
    ├── Reassign
    └── Auto-Reassign
```

The frontend should not separately modify Delivery and YardDock records to simulate assignment.

Use the Dock Operations API.

---

# Relationship with Delivery

Dock ownership is represented through:

```text
Delivery.dock_id
```

Example:

```text
Before:
Delivery.dock_id = null

After:
Delivery.dock_id = 2
```

The selected dock can simultaneously become:

```text
reserved
```

---

# Relationship with Yard Status

The dashboard provides:

```http
GET /dashboard/yard-status
```

which exposes active trailers and their assigned dock state.

Example:

```text
Trailer
   ↓
Delivery
   ↓
Assigned Dock
   ↓
Dock Status
```

---

# Relationship with Trailer-Door Allocation

The dashboard endpoint:

```http
GET /dashboard/trailer-door-allocation
```

compares:

```text
Current Dock
      vs
Scheduled / Recommended Dock
```

and can indicate:

```text
CURRENT_ASSIGNMENT_VALID
REASSIGNMENT_RECOMMENDED
```

Example:

```text
Delivery 2
Current Dock = 1
Dock 1 = blocked
Scheduled Dock = 2
      ↓
REASSIGNMENT_RECOMMENDED
```

---

# Relationship with Operations & Alerts

The Operations layer can detect when a Delivery is assigned to an unusable dock.

Related endpoints include:

```http
POST /operations/detect-dock-unavailable
```

and:

```http
POST /operations/detect-reassignment-required
```

Conceptually:

```text
Delivery
   ↓
Current Dock
   ↓
Dock blocked / maintenance?
   ↓
Operational Problem
   ↓
Reassignment Required
   ↓
Auto-Reassign
```

---

# Frontend Integration

A frontend can use:

```text
Shipment / Trailer
      ↓
GET /dock-operations/recommend/{delivery_id}
      ↓
Show Recommendations
```

For scheduling:

```text
Operations Dashboard
      ↓
GET /dashboard/dock-schedule
      ↓
Display Time Windows
```

For manual assignment:

```text
Operator selects dock
      ↓
POST /dock-operations/assign/{delivery_id}
```

For automatic recovery:

```text
Blocked Dock Detected
      ↓
POST /dock-operations/auto-reassign/{delivery_id}
```

---

# Cross-Team Integration

Another service should treat E2 as the source of truth for dock decision logic.

It should not copy:

```text
Dock Scoring
Scheduling Logic
Reservation Logic
Reassignment Logic
```

into another backend.

Instead:

```text
Need Recommendation
      ↓
Call E2

Need Schedule
      ↓
Call E2

Need Assignment
      ↓
Call E2

Need Automatic Replacement
      ↓
Call E2
```

This keeps dock logic centralized.

---

# Dock Recommendation Router

The project also contains:

```text
app/routers/dock_recommendation.py
```

and the current application registers the dock recommendation router.

That separate interface provides recommendation behavior based on supplied dock candidates and operational request information.

The Delivery-aware operational interface remains:

```http
GET /dock-operations/recommend/{delivery_id}
```

Both APIs should be consumed according to their specific Swagger contracts.

---

# Error Handling

Integrating applications should handle:

| HTTP Status | Meaning |
|---:|---|
| `200` | Successful recommendation/schedule/assignment operation |
| `400` | Invalid dock state or assignment request |
| `404` | Delivery or dock not found |
| `409` | No suitable dock available for automatic reassignment |
| `422` | Request/path/body validation failure |
| `500` | Unexpected backend/database failure |

---

# Example Complete Dock Flow

```text
Shipment approaches yard
      ↓
GET /dock-operations/recommend/{delivery_id}
      ↓
Rank Docks
      ↓
GET /dock-operations/schedule
      ↓
Generate Arrival Window
      ↓
POST /dock-operations/assign/{delivery_id}
      ↓
Dock Reserved
      ↓
Later Dock becomes blocked
      ↓
POST /operations/detect-dock-unavailable
      ↓
POST /operations/detect-reassignment-required
      ↓
POST /dock-operations/auto-reassign/{delivery_id}
      ↓
Replacement Dock Reserved
      ↓
GET /dashboard/trailer-door-allocation
      ↓
Validate Final Allocation
```

---

# Current Limitations

The current Dock Operations implementation does not yet provide:

- persistent schedule records as a separate scheduling table;
- advanced optimization across hundreds of trailers;
- multi-yard routing optimization;
- real dock-service-duration prediction;
- constraint solver / operations-research scheduling;
- authentication/authorization;
- distributed locking for multiple concurrent schedulers.

The current scheduler is designed for the E2 project scope and demonstration workflow.

---

# Summary

Dock Operations provides the operational bridge between incoming shipments and physical yard doors.

```text
Delivery
   ↓
Recommend
   ↓
Schedule
   ↓
Assign
   ↓
Monitor Dock
   ↓
Reassign if Needed
```

The module supports both normal dock assignment and recovery when operational conditions change.
