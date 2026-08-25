# Operations & Alerts API

The Operations API monitors E2 Deliveries for operational problems and manages system-generated alerts.

It supports:

- shipment delay detection;
- shipment exception detection;
- unavailable-dock detection;
- dock-reassignment-required detection;
- operational alert retrieval;
- alert resolution.

**Base path:** `/operations`

---

# Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/operations/detect-delays` | Detect delayed Deliveries |
| POST | `/operations/detect-exceptions` | Detect shipment exceptions |
| POST | `/operations/detect-dock-unavailable` | Detect Deliveries assigned to unusable docks |
| POST | `/operations/detect-reassignment-required` | Detect Deliveries requiring dock reassignment |
| GET | `/operations/alerts` | Get unresolved operational alerts |
| PUT | `/operations/alerts/{alert_id}/resolve` | Resolve an Alert |

---

# Overall Operations Workflow

```text
Delivery
   ↓
Operations Detection
   │
   ├── Delay Detection
   ├── Exception Detection
   ├── Dock Availability Detection
   └── Reassignment Detection
   ↓
Problem Found?
   │
   ├── No
   │    ↓
   │  Continue
   │
   └── Yes
        ↓
Update Delivery / Operational State
        ↓
Create or Reuse Alert
        ↓
GET /operations/alerts
        ↓
Frontend / Operator
        ↓
Take Corrective Action
        ↓
Resolve Alert
```

The Delivery stores current operational state.

Alert records provide actionable notifications for the operations layer.

---

# Alert Object

An Alert contains information such as:

| Field | Type | Description |
|---|---|---|
| `id` | integer | Database-generated Alert ID |
| `delivery_id` | integer / null | Related Delivery |
| `alert_type` | string | Alert category |
| `title` | string | Short alert title |
| `message` | string | Explanation of problem |
| `severity` | string | Alert severity |
| `resolved` | boolean | Resolution state |
| `created_at` | datetime | Alert creation time |

Example:

```json
{
  "severity": "critical",
  "id": 1,
  "message": "GPS location has not been received",
  "created_at": "2026-08-24T11:12:13.088743",
  "delivery_id": 2,
  "alert_type": "exception",
  "title": "Shipment Exception",
  "resolved": false
}
```

---

# 1. Detect Delays

## Endpoint

```http
POST /operations/detect-delays
```

Checks Deliveries for delay conditions.

No request body is required.

---

# Delay Detection Logic

Conceptually:

```text
Load Deliveries
      ↓
Scheduled Arrival available?
      ↓
Estimated Arrival available?
      ↓
Compare Estimated vs Scheduled
      ↓
Late?
  ┌────┴────┐
  No       Yes
            ↓
     delay_detected = true
            ↓
      status = delayed
            ↓
      Create / Reuse Alert
```

The backend can also evaluate overdue shipments when scheduled-arrival information exists and the shipment has not reached an arrival/completion state.

---

# Delivery Side Effects

When a delay is identified, E2 can update:

```text
delivery.delay_detected = true
delivery.status = delayed
```

Therefore the endpoint changes operational shipment state, not only alerts.

---

# Delay Alert

Conceptually:

```text
Delayed Shipment
      ↓
Delivery updated
      ↓
Existing unresolved delay alert?
   ┌──────────┴──────────┐
   Yes                   No
    ↓                     ↓
Do not duplicate      Create Alert
```

The frontend can retrieve alerts through:

```http
GET /operations/alerts
```

---

# Example Delay Response

A response can look conceptually like:

```json
{
  "delayed_shipments": [
    2
  ],
  "count": 1
}
```

---

# Relationship with ML ETA

Delay state can also be influenced by:

```http
POST /eta/predict-delivery/{delivery_id}
```

The ML ETA endpoint predicts arrival and can mark a shipment delayed when predicted lateness exceeds the configured threshold.

Therefore:

```text
ML ETA
   ↓
Predicted Arrival
   ↓
Predicted Delay
   ↓
delay_detected
   ↓
Operations / Alerts
```

---

# 2. Detect Exceptions

## Endpoint

```http
POST /operations/detect-exceptions
```

Checks Deliveries for abnormal shipment conditions.

No request body is required.

---

# Exception Detection

Implemented conditions include cases such as:

- missing GPS information for an in-transit shipment;
- simulation active but coordinates are invalid/missing;
- shipment has reached a relevant yard state but lacks an assigned dock.

---

# Exception 1 — Missing GPS

Conceptually:

```text
Delivery.status = in_transit
        +
last_gps_update is missing
        ↓
Shipment Exception
```

Possible reason:

```text
GPS location has not been received
```

---

# Exception 2 — Invalid GPS During Simulation

```text
simulation_active = true
        +
latitude / longitude missing
        ↓
Shipment Exception
```

Possible reason:

```text
Shipment has invalid GPS coordinates
```

---

# Exception 3 — Missing Dock

A shipment can also become an exception when it reaches a yard-related state but no dock is assigned.

Conceptually:

```text
Shipment reached yard
      +
dock_id = null
      ↓
Operational Exception
```

---

# Exception Side Effects

When an exception is detected:

```text
delivery.exception_detected = true
```

and E2 can create an unresolved exception alert if one does not already exist.

---

# Example Exception Response

```json
{
  "exceptions": [
    {
      "delivery_id": 2,
      "reason": "GPS location has not been received"
    }
  ],
  "count": 1
}
```

---

# 3. Detect Dock Unavailable

## Endpoint

```http
POST /operations/detect-dock-unavailable
```

Checks whether an active Delivery is currently assigned to a dock that can no longer be used.

This endpoint is important because an existing `delivery.dock_id` does not necessarily mean the assignment is still valid.

---

# Unavailable Dock States

Operationally unusable states can include:

```text
blocked
maintenance
```

and other states considered unsuitable by the current dock logic.

---

# Detection Flow

```text
Delivery
   ↓
Has dock_id?
   ├── No → Ignore
   │
   └── Yes
        ↓
Load YardDock
        ↓
Check Dock Status
        ↓
Usable?
   ┌────┴────┐
   Yes       No
    ↓         ↓
Continue   Report Delivery
```

---

# Example Request

```http
POST /operations/detect-dock-unavailable
```

No request body is required.

---

# Example Response

This response was produced during testing:

```json
{
  "dock_unavailable": [
    {
      "delivery_id": 2,
      "tracking_number": "TR-2045",
      "trailer_id": null,
      "dock_id": 1,
      "dock_number": "D-01",
      "dock_status": "blocked"
    }
  ],
  "count": 1
}
```

---

# Response Fields

| Field | Type | Description |
|---|---|---|
| `delivery_id` | integer | Delivery using the unavailable dock |
| `tracking_number` | string / null | Shipment tracking number |
| `trailer_id` | string / null | Trailer identifier |
| `dock_id` | integer | Current dock ID |
| `dock_number` | string | Current dock number |
| `dock_status` | string | Operational state causing the problem |

---

# Example Scenario

```text
Delivery 2
    ↓
dock_id = 1
    ↓
Dock 1 status = blocked
    ↓
POST /operations/detect-dock-unavailable
    ↓
Delivery 2 returned as dock_unavailable
```

---

# Relationship with Yard Docks

A dock can be updated through:

```http
PUT /yard-docks/{dock_id}?status=blocked
```

Then:

```http
POST /operations/detect-dock-unavailable
```

can identify Deliveries affected by that change.

Conceptually:

```text
Yard Operator
     ↓
Block Dock
     ↓
Operations Detection
     ↓
Affected Deliveries
```

---

# 4. Detect Reassignment Required

## Endpoint

```http
POST /operations/detect-reassignment-required
```

Checks whether a Delivery's current dock assignment is no longer operationally valid and the Delivery should be reassigned.

---

# Example Request

```http
POST /operations/detect-reassignment-required
```

No request body is required.

---

# Detection Flow

```text
Delivery
    ↓
Current Dock
    ↓
Check Dock State
    ↓
Dock still usable?
   ┌─────┴─────┐
  Yes          No
   ↓            ↓
Normal      Reassignment Required
```

---

# Example Response

This response was produced during E2 testing:

```json
{
  "reassignment_required": [
    {
      "delivery_id": 2,
      "tracking_number": "TR-2045",
      "trailer_id": null,
      "current_dock_id": 1,
      "current_dock_number": "D-01",
      "dock_status": "blocked",
      "reassignment_required": true
    }
  ],
  "count": 1
}
```

---

# Response Fields

| Field | Type | Description |
|---|---|---|
| `delivery_id` | integer | Delivery requiring reassignment |
| `tracking_number` | string / null | Shipment tracking number |
| `trailer_id` | string / null | Trailer ID |
| `current_dock_id` | integer | Existing dock |
| `current_dock_number` | string | Existing dock number |
| `dock_status` | string | Current dock state |
| `reassignment_required` | boolean | Whether replacement assignment is needed |

---

# Dock-Unavailable vs Reassignment-Required

These endpoints are related but represent different operational questions.

## Dock Unavailable

Answers:

```text
Which Deliveries are currently attached
to unusable docks?
```

Endpoint:

```http
POST /operations/detect-dock-unavailable
```

---

## Reassignment Required

Answers:

```text
Which Deliveries now need a new dock?
```

Endpoint:

```http
POST /operations/detect-reassignment-required
```

Conceptually:

```text
Dock becomes blocked
       ↓
detect-dock-unavailable
       ↓
Problem identified
       ↓
detect-reassignment-required
       ↓
Replacement required
```

---

# Automatic Remediation

After reassignment is identified, E2 can automatically select another dock through:

```http
POST /dock-operations/auto-reassign/{delivery_id}
```

Full flow:

```text
Dock Blocked
      ↓
detect-dock-unavailable
      ↓
detect-reassignment-required
      ↓
auto-reassign
      ↓
Alternative Dock Selected
      ↓
Delivery.dock_id updated
```

---

# Example Tested Reassignment Flow

During testing:

```text
Delivery 2
    ↓
Current Dock = 1
    ↓
Dock 1 = blocked
    ↓
Reassignment required = true
```

The dock scheduler then selected:

```text
Dock 2
```

as the usable alternative.

---

# Relationship with Dock Scheduling

The scheduler:

```http
GET /dock-operations/schedule
```

or:

```http
GET /dashboard/dock-schedule
```

does not preserve a blocked assignment as valid.

Conceptually:

```text
Current Dock = blocked
       ↓
Scheduler rejects current dock
       ↓
Evaluate alternatives
       ↓
Select suitable replacement
```

---

# Relationship with Trailer-Door Allocation

The dashboard endpoint:

```http
GET /dashboard/trailer-door-allocation
```

combines current and scheduled assignments.

Example:

```text
Current Dock = 1
Current Dock Status = blocked

Scheduled Dock = 2

reassignment_required = true

allocation_status =
REASSIGNMENT_RECOMMENDED
```

This allows the frontend to show both the problem and the proposed operational correction.

---

# 5. Get Alerts

## Endpoint

```http
GET /operations/alerts
```

Returns active unresolved alerts.

---

# Example Request

```http
GET /operations/alerts
```

---

# Example Response

```json
[
  {
    "severity": "critical",
    "id": 1,
    "message": "GPS location has not been received",
    "created_at": "2026-08-24T11:12:13.088743",
    "delivery_id": 2,
    "alert_type": "exception",
    "title": "Shipment Exception",
    "resolved": false
  }
]
```

The `delivery_id` allows another system to resolve the affected shipment.

---

# Alert-to-Delivery Relationship

```text
Alert
  │
  │ delivery_id
  ▼
Delivery
```

Example:

```json
{
  "id": 1,
  "delivery_id": 2,
  "title": "Shipment Exception"
}
```

means Alert `1` belongs to Delivery `2`.

---

# 6. Resolve Alert

## Endpoint

```http
PUT /operations/alerts/{alert_id}/resolve
```

Marks an existing Alert as resolved.

---

# Path Parameter

| Parameter | Type | Required | Description |
|---|---|---:|---|
| `alert_id` | integer | Yes | Alert database ID |

---

# Example Request

```http
PUT /operations/alerts/1/resolve
```

No request body is required.

---

# Backend Logic

```text
Receive alert_id
      ↓
Find Alert
      ↓
Alert exists?
  No → HTTP 404
      ↓ Yes
resolved = true
      ↓
Commit
      ↓
Return Success
```

---

# Example Successful Response

```json
{
  "message": "Alert resolved successfully",
  "alert_id": 1
}
```

---

# Important Resolution Behavior

Resolving an Alert means:

```text
alert.resolved = true
```

It does **not** automatically repair the underlying problem.

For example:

```text
Dock Blocked
    ↓
Alert / Detection
    ↓
Resolve Alert
```

does not make the dock available.

The underlying dock still needs an operational action such as:

```http
PUT /yard-docks/{dock_id}
```

or:

```http
POST /dock-operations/auto-reassign/{delivery_id}
```

---

# Duplicate Alert Protection

The backend checks for unresolved alerts before creating another equivalent alert for the same Delivery and alert type.

Conceptually:

```text
Problem detected
      ↓
Existing unresolved matching alert?
   ┌─────────┴─────────┐
  Yes                  No
   ↓                    ↓
Reuse               Create
```

This prevents repeated detection calls from creating unnecessary duplicate alerts.

---

# Relationship with Tracking

Tracking provides shipment GPS state.

Operations evaluates that state.

```text
Tracking
   ↓
GPS Information
   ↓
Operations
   ↓
Missing GPS?
   ↓
Exception
```

---

# Relationship with ETA

ML ETA prediction can identify a future delay.

```text
ETA Prediction
      ↓
Estimated Arrival
      ↓
Compare Scheduled Arrival
      ↓
Predicted Delay
      ↓
Delivery.delay_detected
      ↓
Operations / Alert
```

---

# Relationship with Yard Docks

Yard Docks provides current dock state.

```text
YardDock
   ↓
available / reserved / blocked / maintenance
   ↓
Operations
   ↓
Availability Evaluation
```

---

# Relationship with Dock Operations

Operations identifies problems.

Dock Operations performs corrective assignment.

```text
Operations
   ↓
Problem Detected
   ↓
Dock Operations
   ↓
Assignment / Reassignment
```

---

# Relationship with Dashboard

Dashboard endpoints expose the resulting operational state.

Useful endpoints include:

```http
GET /dashboard/summary
GET /dashboard/yard-status
GET /dashboard/dock-schedule
GET /dashboard/trailer-door-allocation
GET /dashboard/insights
```

Conceptually:

```text
Tracking + ETA + Docks
        ↓
Operations
        ↓
Alerts / Flags
        ↓
Dashboard
```

---

# Frontend Integration

An Operations UI can use:

```text
Page Load / Poll
      ↓
GET /operations/alerts
      ↓
Render Operational Alerts
```

For dock problems:

```text
POST /operations/detect-dock-unavailable
      ↓
POST /operations/detect-reassignment-required
      ↓
Display affected shipment
      ↓
POST /dock-operations/auto-reassign/{delivery_id}
```

---

# Example UI Flow

```text
CRITICAL

Dock Unavailable

Delivery #2
Tracking: TR-2045
Current Dock: D-01
Dock Status: BLOCKED

[View Shipment]
[Reassign Dock]
```

---

# Cross-Team Integration

Another service does not need to know the Python implementation.

It only needs the API contract.

Example:

```text
External Operations Service
       ↓
POST detection endpoints
       ↓
Read response
       ↓
Use delivery_id
       ↓
GET /tracking/shipment/id/{delivery_id}
       ↓
Take corrective action
```

---

# Recommended Operations Sequence

A complete operational check can run:

```text
1. POST /operations/detect-delays

2. POST /operations/detect-exceptions

3. POST /operations/detect-dock-unavailable

4. POST /operations/detect-reassignment-required

5. GET /operations/alerts

6. GET /dashboard/trailer-door-allocation
```

If reassignment is required:

```text
7. POST /dock-operations/auto-reassign/{delivery_id}
```

Then verify:

```text
8. GET /yard-docks/

9. GET /dashboard/dock-schedule

10. GET /dashboard/trailer-door-allocation
```

---

# Error Handling

Integrating applications should handle:

| HTTP Status | Meaning |
|---:|---|
| `200` | Detection/read/resolve completed |
| `404` | Resource not found |
| `400` | Invalid operational condition/request |
| `422` | Request/path validation error |
| `500` | Unexpected backend failure |

FastAPI errors generally use:

```json
{
  "detail": "Error message"
}
```

---

# Current Limitations

The current Operations API provides rule-based operational monitoring.

It does not yet provide:

- predictive ML exception classification;
- email/SMS notification delivery;
- push notifications;
- WebSocket alert streaming;
- automatic remediation for every problem;
- persistent workflow/escalation rules;
- alert ownership/assignment;
- authentication/authorization.

However, dock reassignment is partially automatable through:

```http
POST /dock-operations/auto-reassign/{delivery_id}
```

---

# Summary

The Operations API acts as E2's operational monitoring layer.

```text
Tracking
+
ETA
+
Delivery State
+
Dock State
      ↓
Operations
      ↓
Delay
Exception
Dock Unavailable
Reassignment Required
      ↓
Alerts / Corrective Action
      ↓
Dashboard
```

It converts raw logistics state into actionable operational information.
