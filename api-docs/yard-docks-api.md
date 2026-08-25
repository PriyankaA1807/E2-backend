# Yard Docks API

The Yard Docks API manages the physical dock records available inside E2 yards.

Dock records are used by:

- Delivery
- Dock Operations
- Dock Scheduling
- Trailer-Door Allocation
- Operations & Alerts
- Dashboard
- WMS-style simulation feed

**Base path:** `/yard-docks`

---

# Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/yard-docks/` | Create a Yard Dock |
| GET | `/yard-docks/` | Get all Yard Docks |
| GET | `/yard-docks/{dock_id}` | Get one Yard Dock |
| PUT | `/yard-docks/{dock_id}` | Update Dock status |
| DELETE | `/yard-docks/{dock_id}` | Delete a Yard Dock |

---

# Yard Dock Object

A Yard Dock stores information about a physical loading/unloading door and its operational capabilities.

| Field | Type | Description |
|---|---|---|
| `id` | integer | Database-generated Dock ID |
| `yard_name` | string | Yard containing the dock |
| `dock_number` | string | Dock identifier |
| `status` | string | Current operational state |
| `dock_type` | string | Dock type |
| `supported_vehicle_type` | string | Supported vehicle type |
| `max_vehicle_length` | float | Maximum supported vehicle length |
| `refrigerated` | boolean | Refrigeration support |
| `hazardous_allowed` | boolean | Hazardous-load support |

These capability fields are used by recommendation and scheduling logic.

---

# 1. Create Yard Dock

## Endpoint

```http
POST /yard-docks/
```

Creates a new Yard Dock.

---

## Request Body

```json
{
  "yard_name": "Main Warehouse",
  "dock_number": "D-01",
  "status": "available",
  "dock_type": "standard",
  "supported_vehicle_type": "truck",
  "max_vehicle_length": 20,
  "refrigerated": false,
  "hazardous_allowed": false
}
```

---

## Successful Response

```http
201 Created
```

Example:

```json
{
  "yard_name": "Main Warehouse",
  "dock_number": "D-01",
  "status": "available",
  "dock_type": "standard",
  "supported_vehicle_type": "truck",
  "max_vehicle_length": 20,
  "refrigerated": false,
  "hazardous_allowed": false,
  "id": 1
}
```

---

# 2. Get All Yard Docks

## Endpoint

```http
GET /yard-docks/
```

Returns all Yard Dock records.

---

## Example Request

```http
GET /yard-docks/
```

---

## Example Response

```json
[
  {
    "yard_name": "Main Warehouse",
    "dock_number": "D-01",
    "status": "blocked",
    "dock_type": "standard",
    "supported_vehicle_type": "truck",
    "max_vehicle_length": 20,
    "refrigerated": false,
    "hazardous_allowed": false,
    "id": 1
  },
  {
    "yard_name": "Kolkata Main Yard",
    "dock_number": "D-01",
    "status": "reserved",
    "dock_type": "standard",
    "supported_vehicle_type": "truck",
    "max_vehicle_length": 20,
    "refrigerated": false,
    "hazardous_allowed": false,
    "id": 2
  }
]
```

---

# 3. Get Yard Dock by ID

## Endpoint

```http
GET /yard-docks/{dock_id}
```

Returns a single Yard Dock.

---

## Path Parameter

| Parameter | Type | Required | Description |
|---|---|---:|---|
| `dock_id` | integer | Yes | Yard Dock database ID |

---

## Example

```http
GET /yard-docks/1
```

---

## Yard Dock Not Found

```http
404 Not Found
```

Example:

```json
{
  "detail": "Yard/Dock not found"
}
```

---

# 4. Update Yard Dock Status

## Endpoint

```http
PUT /yard-docks/{dock_id}
```

Updates the operational status of an existing Yard Dock.

This route updates **status only**.

---

## Path Parameter

| Parameter | Type | Required |
|---|---|---:|
| `dock_id` | integer | Yes |

---

## Query Parameter

| Parameter | Type | Required |
|---|---|---:|
| `status` | string | Yes |

---

## Example

```http
PUT /yard-docks/1?status=blocked
```

---

# Supported Dock Status Values

```text
available
occupied
reserved
maintenance
blocked
```

The backend normalizes the supplied value before validation.

Example:

```text
BLOCKED
   ↓
blocked
```

---

# Dock Status Meaning

## `available`

Dock can be selected for a new assignment.

## `reserved`

Dock is currently reserved for a Delivery.

## `occupied`

Dock is physically occupied.

## `maintenance`

Dock is unavailable because of maintenance.

## `blocked`

Dock is unavailable for operational use.

---

# Backend Update Logic

```text
Receive dock_id + status
        ↓
Find Yard Dock
        ↓
Dock exists?
   No → 404
        ↓ Yes
Normalize Status
        ↓
Allowed?
   No → 400
        ↓ Yes
Update Dock
        ↓
Commit
        ↓
Return Updated Dock
```

---

# Example Status Update

```http
PUT /yard-docks/1?status=blocked
```

Response:

```json
{
  "yard_name": "Main Warehouse",
  "dock_number": "D-01",
  "status": "blocked",
  "dock_type": "standard",
  "supported_vehicle_type": "truck",
  "max_vehicle_length": 20,
  "refrigerated": false,
  "hazardous_allowed": false,
  "id": 1
}
```

---

# Operational Impact of Status Changes

Changing a dock's status can affect active Deliveries.

For example:

```text
Delivery 2
   ↓
dock_id = 1

Dock 1
   ↓
status changes:
reserved → blocked
```

This means the Delivery still references Dock 1, but the dock is no longer operationally usable.

E2 can then detect the issue through:

```http
POST /operations/detect-dock-unavailable
```

and:

```http
POST /operations/detect-reassignment-required
```

---

# 5. Delete Yard Dock

## Endpoint

```http
DELETE /yard-docks/{dock_id}
```

Deletes an existing Yard Dock.

---

## Example

```http
DELETE /yard-docks/1
```

---

# Occupied Dock Protection

A dock whose status is:

```text
occupied
```

cannot be deleted.

The backend returns:

```http
400 Bad Request
```

Example:

```json
{
  "detail": "Cannot delete an occupied dock"
}
```

---

# Successful Delete

```json
{
  "message": "Yard/Dock deleted successfully"
}
```

---

# Delivery Relationship

A Delivery can reference a Yard Dock through:

```text
Delivery.dock_id
```

Relationship:

```text
YardDock
   ↑
   │ dock_id
   │
Delivery
```

A Delivery may initially have:

```text
dock_id = null
```

This allows dock allocation to happen later.

---

# Normal Dock Lifecycle

Conceptually:

```text
Delivery Created
      ↓
dock_id = null
      ↓
Shipment Approaches Yard
      ↓
Dock Recommendation
      ↓
Dock Scheduling
      ↓
Dock Assignment
      ↓
Dock.status = reserved
      ↓
Delivery.dock_id = selected dock
```

---

# Dock Operations Integration

The Yard Docks API manages dock records.

The Dock Operations API performs operational decisions.

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

Related endpoints:

```http
GET /dock-operations/recommend/{delivery_id}
GET /dock-operations/schedule
POST /dock-operations/assign/{delivery_id}
POST /dock-operations/reassign/{delivery_id}
POST /dock-operations/auto-reassign/{delivery_id}
```

---

# Dock Recommendation Relationship

Dock configuration affects recommendation scores.

Examples:

```text
status
supported_vehicle_type
dock_type
refrigerated
hazardous_allowed
max_vehicle_length
```

A dock that is:

```text
blocked
maintenance
occupied
```

should not be treated as a normal available recommendation.

---

# Dock Scheduling Relationship

Dock scheduling uses YardDock state to determine whether a dock can receive an incoming trailer.

Conceptually:

```text
Incoming Delivery
      ↓
Effective Arrival
      ↓
Load Yard Docks
      ↓
Check Operational State
      ↓
Usable Dock?
      ↓
Generate Time Slot
```

Current schedule endpoint:

```http
GET /dock-operations/schedule
```

and dashboard equivalent:

```http
GET /dashboard/dock-schedule
```

---

# Blocked Dock Scheduling Behavior

A blocked dock should not be preserved as a valid current assignment.

Example:

```text
Delivery 2
   ↓
Current Dock = 1
   ↓
Dock 1 = blocked
   ↓
Scheduler rejects Dock 1
   ↓
Alternative Dock evaluated
   ↓
Dock 2 selected
```

---

# Dock Assignment Side Effect

When assigned through:

```http
POST /dock-operations/assign/{delivery_id}
```

the selected dock becomes:

```text
reserved
```

and the Delivery receives:

```text
dock_id = selected dock ID
```

---

# Manual Reassignment

Manual reassignment:

```http
POST /dock-operations/reassign/{delivery_id}
```

Conceptually:

```text
Old Dock
      ↓
Release old reservation when appropriate

New Dock
      ↓
reserved

Delivery
      ↓
dock_id = new dock
```

---

# Important Old Dock Behavior

If the old dock is:

```text
reserved
```

it can be released to:

```text
available
```

But if the old dock is:

```text
blocked
maintenance
```

its operational problem should remain.

Changing the Delivery assignment should not incorrectly reset a blocked dock to available.

---

# Automatic Reassignment

E2 supports:

```http
POST /dock-operations/auto-reassign/{delivery_id}
```

This endpoint:

```text
Finds Delivery
      ↓
Loads Available Docks
      ↓
Excludes Current Dock
      ↓
Scores Candidates
      ↓
Selects Best Alternative
      ↓
Reserves New Dock
      ↓
Updates Delivery
```

---

# Operations Integration

YardDock state is used by Operations.

Related endpoints:

```http
POST /operations/detect-dock-unavailable
POST /operations/detect-reassignment-required
```

Example:

```text
Dock 1
status = blocked
       ↓
Delivery 2 uses Dock 1
       ↓
detect-dock-unavailable
       ↓
Delivery 2 returned
       ↓
detect-reassignment-required
       ↓
reassignment_required = true
```

---

# Trailer-Door Allocation

The Dashboard exposes:

```http
GET /dashboard/trailer-door-allocation
```

This compares:

```text
Current Dock
      vs
Scheduled / Recommended Dock
```

Example:

```text
Current Dock:
Dock 1
BLOCKED

Recommended Dock:
Dock 2

Result:
REASSIGNMENT_RECOMMENDED
```

---

# Yard Status Integration

Current trailer-to-dock state is also available through:

```http
GET /dashboard/yard-status
```

Each trailer can include:

```text
assigned_dock
dock_status
dock_type
yard_name
dock_number
```

---

# Dashboard Dock Status

Dock information is exposed through:

```http
GET /dashboard/dock-status
```

The dashboard can show:

```text
available
reserved
occupied
blocked
maintenance
```

---

# Dashboard Summary

The dashboard summary can aggregate dock states.

Conceptually:

```text
total
available
occupied
reserved
blocked
maintenance
```

The exact response should follow the running Swagger/OpenAPI schema.

---

# Simulated WMS Feed

Dock information can also appear in:

```http
GET /simulation/wms-feed
```

This provides a combined operational feed containing:

```text
Trailers
+
Docks
```

Useful for:

- frontend demos;
- WMS-like integration testing;
- yard capacity visibility.

---

# Frontend Integration

A Yard Management screen can load:

```text
GET /yard-docks/
      ↓
Render Dock Cards
```

Example:

```text
D-01
BLOCKED

D-02
RESERVED

D-03
AVAILABLE
```

For scheduling:

```text
GET /dashboard/dock-schedule
```

For assignment:

```text
POST /dock-operations/assign/{delivery_id}
```

For automatic recovery:

```text
POST /dock-operations/auto-reassign/{delivery_id}
```

---

# Status Update UI

Typical flow:

```text
Operator selects Dock
      ↓
Changes status
      ↓
PUT /yard-docks/{dock_id}?status=blocked
      ↓
Backend validates
      ↓
Dock updated
      ↓
Operations / Dashboard reflect change
```

---

# Cross-Team Integration

Another system primarily needs to understand:

```text
Dock ID
Dock Status
Dock Capabilities
```

Supported operational statuses:

```text
available
reserved
occupied
maintenance
blocked
```

Another service should not manually update:

```text
Delivery.dock_id
```

to perform assignment.

Use Dock Operations APIs so E2 maintains consistent state.

---

# Error Handling

| HTTP Status | Meaning |
|---:|---|
| `200` | Successful read/update/delete |
| `201` | Yard Dock created |
| `400` | Invalid status / invalid delete operation |
| `404` | Yard Dock not found |
| `422` | Request/path/query validation failure |
| `500` | Unexpected backend/database failure |

FastAPI errors generally use:

```json
{
  "detail": "Error message"
}
```

---

# Current Limitations

The Yard Docks API currently does not provide:

- pagination;
- search/filtering;
- full dock configuration editing through PUT;
- authentication/authorization;
- automatic physical occupancy sensors;
- dock utilization history;
- persistent dock-capacity analytics;
- yard-specific access control.

Dock recommendation, scheduling, assignment, and reassignment are handled by the Dock Operations layer.

---

# Summary

The Yard Docks API acts as E2's dock master-data and operational-status layer.

```text
YardDock Configuration
        ↓
Dock Status
        ↓
Recommendation
        ↓
Scheduling
        ↓
Assignment / Reassignment
        ↓
Operations / Dashboard
```

Use `/yard-docks` for dock configuration/status, and `/dock-operations` for operational allocation decisions.
