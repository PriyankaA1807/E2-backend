# Operations API

API documentation for the **Operations & Alerts** module of the E2 Smart Restock & Yard Dock Delivery Tracker.

This module handles operational monitoring, delay detection, shipment exceptions, alerts, and operational insights.

For the hackathon version, the system uses **one Operations Admin view**. All operational alerts are available to this admin dashboard. A complex multi-user authentication or role-management system is not required.

---

## Base URL

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

> Replace the local URL with the deployed backend URL after deployment.

---

# Overview

The Operations module monitors inbound deliveries and identifies operational problems such as:

* Predicted shipment delays
* Missing GPS updates
* Shipment exceptions
* Dock availability problems
* Dock reassignment requirements

When a problem is detected, the backend can create an operational alert.

For the hackathon architecture:

```text
Truck / Delivery
       ↓
Tracking + ETA
       ↓
Problem Detected
       ↓
Operational Alert
       ↓
Single Operations Admin Dashboard
```

---

# Single Operations Admin

The hackathon version does not require:

```text
Multiple users
Multiple operations roles
Role-based alert routing
Complex authentication
Individual notification accounts
```

Instead, the project uses one logical:

```text
Operations Admin
```

All unresolved operational alerts can be displayed in the same Operations Admin dashboard.

This keeps the prototype focused on logistics operations rather than authentication infrastructure.

---

# Alert Types

Operational alerts can represent situations such as:

```text
delay
exception
dock_unavailable
dock_reassignment
```

The exact alert types depend on the operational condition detected by the backend.

---

# Alert Severity

Alerts can contain severity levels such as:

```text
low
medium
high
critical
```

Severity helps the Operations Admin understand which issues require attention first.

---

# 1. Detect Delays

## Endpoint

```http
POST /operations/detect-delays
```

Checks active deliveries for delay conditions.

The system compares the delivery's expected or estimated arrival against its scheduled arrival.

---

## Delay Flow

```text
Active Delivery
      ↓
Read Scheduled Arrival
      ↓
Read Estimated Arrival / ETA
      ↓
Compare Times
      ↓
Late?
   ↙     ↘
 NO      YES
          ↓
   delay_detected = true
          ↓
      Delay Alert
```

---

## Delay Detection During Simulation

Delay detection can also happen while the truck is automatically moving.

The flow is:

```text
Truck Moves
    ↓
Distance Changes
    ↓
ETA Recalculated
    ↓
Estimated Arrival Changes
    ↓
Delay Condition Checked
    ↓
Alert Created if Required
```

Therefore, the Operations Admin can see a delay while the simulated truck is still travelling.

---

# 2. Detect Shipment Exceptions

## Endpoint

```http
POST /operations/detect-exceptions
```

Checks deliveries for operational exceptions.

One example is missing or stale GPS information.

---

## Example Exception

A delivery may require attention when the backend has not received a valid GPS location.

Example alert:

```json
{
  "alert_type": "exception",
  "severity": "critical",
  "title": "Shipment Exception",
  "message": "GPS location has not been received",
  "resolved": false
}
```

---

# 3. Get Operational Alerts

## Endpoint

```http
GET /operations/alerts
```

Returns operational alerts.

For the hackathon frontend, this endpoint can be used by the **single Operations Admin dashboard**.

---

## Example Response

```json
[
  {
    "severity": "high",
    "id": 1,
    "message": "Trailer TRL-101 is predicted to arrive late.",
    "delivery_id": 3,
    "alert_type": "delay",
    "title": "Predicted Shipment Delay",
    "resolved": false,
    "created_at": "2026-08-26T10:00:00"
  }
]
```

The exact response depends on the alerts currently stored in the database.

---

# Who Receives the Alerts?

For this hackathon project, alerts are not routed to many different users.

Instead:

```text
Delay / Exception / Dock Problem
             ↓
         Alert Table
             ↓
GET /operations/alerts
             ↓
Operations Admin Dashboard
```

So when explaining the project, say:

> All operational alerts are centralized in one Operations Admin dashboard for the hackathon prototype.

The current backend alert records are therefore treated as dashboard alerts rather than user-specific notifications.

---

# 4. Resolve Alert

## Endpoint

```http
PUT /operations/alerts/{alert_id}/resolve
```

Marks an operational alert as resolved.

---

## Path Parameter

| Parameter  | Type    | Required | Description                   |
| ---------- | ------- | -------- | ----------------------------- |
| `alert_id` | integer | Yes      | Alert that should be resolved |

---

## Example Request

```http
PUT /operations/alerts/1/resolve
```

---

## Result

After resolution:

```text
resolved = true
```

This allows the Operations Admin to distinguish active problems from issues that have already been handled.

---

# Alert Lifecycle

The basic alert lifecycle is:

```text
Operational Condition
        ↓
Problem Detected
        ↓
Alert Created
        ↓
resolved = false
        ↓
Operations Admin Sees Alert
        ↓
Admin Handles Problem
        ↓
Resolve Alert Endpoint
        ↓
resolved = true
```

---

# Duplicate Alert Prevention

The backend should avoid creating repeated unresolved alerts for the same ongoing problem.

For example:

```text
Truck delayed
    ↓
Alert created
    ↓
Background loop checks again
    ↓
Same unresolved delay already exists
    ↓
Do not create another identical alert
```

This prevents the Operations Admin dashboard from being flooded with duplicate alerts while the background tracker continues running.

---

# Relationship With ETA

The Operations module works closely with ETA prediction.

```text
GPS Position
     ↓
Remaining Distance
     ↓
Random Forest ETA
     ↓
Estimated Arrival
     ↓
Compare With Scheduled Arrival
     ↓
Delay?
     ↓
Operational Alert
```

This allows ETA predictions to become actionable operational information.

---

# Relationship With GPS Simulation

The automatic GPS simulation continuously changes the truck's location.

As the truck moves:

```text
Latitude / Longitude
       ↓
Distance
       ↓
ETA
       ↓
Delay Detection
       ↓
Alerts
```

This means the Operations Admin dashboard can reflect changes produced by the simulated real-time tracking system.

---

# Relationship With Dock Operations

Operational alerts can also support yard and dock management.

For example:

```text
Truck Approaching Yard
       ↓
Check Dock
       ↓
Assigned Dock Unavailable
       ↓
Reassignment Required
       ↓
Operational Alert
       ↓
Operations Admin
```

The admin can then use the dock recommendation or reassignment APIs.

---

# Frontend Integration

A frontend Operations Admin dashboard can periodically retrieve:

```http
GET /operations/alerts
```

and display unresolved alerts.

The dashboard may show:

```text
Alert Severity
Alert Type
Delivery ID
Trailer
Alert Message
Created Time
Resolved Status
```

The same dashboard can combine alert information with tracking, ETA, yard, and dock information.

---

# Suggested Dashboard Flow

```text
Operations Admin Dashboard
          ↓
Get Active Deliveries
          ↓
Get Current Tracking Data
          ↓
Display Truck Map
          ↓
Display ETA
          ↓
GET /operations/alerts
          ↓
Display Active Alerts
          ↓
Admin Handles Issue
          ↓
PUT /operations/alerts/{alert_id}/resolve
```

---

# Hackathon Scope

The Operations module intentionally avoids unnecessary enterprise complexity.

For the hackathon:

```text
One Operations Admin
One central alert list
No multi-role authentication
No individual alert recipients
No SMS/email notification infrastructure required
```

The focus is demonstrating:

```text
Detect Problem
      ↓
Create Alert
      ↓
Show Admin
      ↓
Resolve Problem
```

---

# Production Extension

In a production system, the same alert architecture could later support:

* Multiple operations users
* Role-based access control
* Warehouse-specific administrators
* Email notifications
* SMS notifications
* Push notifications
* Slack or Microsoft Teams notifications
* Escalation policies
* Alert ownership
* Audit history

These features are outside the scope of the current hackathon prototype.

---

# Demo Explanation

During the hackathon demo, the alert system can be explained as:

> The backend continuously monitors the simulated truck. As its location changes, the ETA is recalculated. If the predicted arrival indicates a delay or another operational exception occurs, the backend creates an alert. All alerts are centralized in a single Operations Admin dashboard, where the admin can view and resolve them.

---

# Example End-to-End Delay Scenario

```text
Truck Simulation Started
        ↓
Truck Moves Automatically
        ↓
GPS Position Updated
        ↓
Remaining Distance Calculated
        ↓
Random Forest ETA Updated
        ↓
Predicted Arrival Is Late
        ↓
delay_detected = true
        ↓
Delay Alert Created
        ↓
Operations Admin Sees Alert
        ↓
Admin Handles Situation
        ↓
Alert Resolved
```

---

# Example Arrival Scenario

When the truck reaches the yard:

```text
Truck Reaches Destination
        ↓
status = arrived_at_gate
        ↓
distance_remaining_km = 0
        ↓
eta_minutes = 0
        ↓
simulation_active = false
        ↓
Operations Continues With Yard / Dock Process
```

A previous delay can remain recorded as historical information even after the truck arrives.

---

# Summary

The Operations API provides:

* Delay detection
* Shipment exception detection
* Operational alerts
* Alert resolution
* Integration with ETA prediction
* Integration with automatic GPS simulation
* Integration with dock operations
* Centralized alert visibility

For the hackathon, all operational alerts are presented through **one Operations Admin view**, without requiring a complex user-authentication or role-management system.
