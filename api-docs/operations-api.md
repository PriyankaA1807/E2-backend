# Operations & Alerts API

The Operations API monitors Deliveries for operational problems and manages system-generated alerts.

It provides two main detection workflows:

* **Delay detection** — identifies shipments that have exceeded their expected arrival.
* **Exception detection** — identifies abnormal shipment conditions such as missing GPS information or missing dock assignment.

It also provides APIs to retrieve and resolve generated alerts.

**Base path:** `/operations`

---

## Endpoints

| Method | Endpoint                                | Purpose                                      |
| ------ | --------------------------------------- | -------------------------------------------- |
| POST   | `/operations/detect-delays`             | Detect delayed Deliveries and create alerts  |
| POST   | `/operations/detect-exceptions`         | Detect shipment exceptions and create alerts |
| GET    | `/operations/alerts`                    | Get operational alerts                       |
| PUT    | `/operations/alerts/{alert_id}/resolve` | Resolve an Alert                             |

---

# Overall Operations Workflow

```text
Delivery
   ↓
Operations Detection
   │
   ├── Delay Detection
   │
   └── Exception Detection
   ↓
Problem Found?
   │
   ├── No → No Alert
   │
   └── Yes
         ↓
   Update Delivery flags/status
         ↓
      Create Alert
         ↓
GET /operations/alerts
         ↓
Frontend / Operator
         ↓
Resolve Alert
```

The Delivery stores the current operational state, while Alert records provide actionable notifications for the operations team.

---

# Alert Object

An Alert contains information such as:

| Field         | Type     | Description                         |
| ------------- | -------- | ----------------------------------- |
| `id`          | integer  | Database-generated Alert ID         |
| `delivery_id` | integer  | Delivery associated with the Alert  |
| `alert_type`  | string   | Type/category of Alert              |
| `title`       | string   | Short Alert title                   |
| `message`     | string   | Description of the detected problem |
| `severity`    | string   | Alert severity                      |
| `resolved`    | boolean  | Whether the Alert has been resolved |
| `created_at`  | datetime | Time the Alert was created          |

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

# Detect Delays

## `POST /operations/detect-delays`

Checks Deliveries for delay conditions.

No request body is required.

### Example Request

```http
POST /operations/detect-delays
```

---

# Delay Detection Logic

Conceptually:

```text
Load Deliveries
      ↓
Check expected/scheduled arrival
      ↓
Compare with current time
      ↓
Shipment overdue?
   No → Continue
      ↓ Yes
Mark Delivery delayed
      ↓
Set delay_detected
      ↓
Create Delay Alert
```

The operation allows E2 to convert shipment timing information into an operational warning.

---

# Delivery Side Effects

When a Delivery satisfies the implemented delay condition, the backend can update:

```text
delivery.status = "delayed"

delivery.delay_detected = true
```

Therefore delay detection changes more than the Alert table.

The Delivery itself becomes marked as delayed.

---

# Delay Alert

When a delay is detected, an Alert is generated for that Delivery.

Conceptually:

```text
Delivery Overdue
      ↓
status = delayed
delay_detected = true
      ↓
Delay Alert
```

The frontend can then retrieve that Alert using:

```http
GET /operations/alerts
```

---

# Duplicate Delay Protection

The backend uses the Delivery's detection flag to avoid repeatedly treating the same Delivery as a newly detected delay.

Conceptually:

```text
Delivery delayed
      ↓
delay_detected already true?
      │
      ├── Yes → Do not treat as new detection
      │
      └── No
            ↓
      Mark + Create Alert
```

This is important if the detection endpoint is called repeatedly.

---

# Detect Exceptions

## `POST /operations/detect-exceptions`

Checks Deliveries for operational exception conditions.

No request body is required.

### Example Request

```http
POST /operations/detect-exceptions
```

---

# Exception Detection Logic

The current backend checks shipment conditions that indicate an abnormal operational state.

The implemented checks include missing shipment GPS information and missing Dock assignment in relevant shipment states.

---

# Exception 1 — Missing GPS

A shipment can be considered an exception when it is in transit but GPS information has not been received.

Conceptually:

```text
Delivery status = in_transit
        +
GPS location/update missing
        ↓
Shipment Exception
```

An Alert can be created with information such as:

```text
Title:
Shipment Exception

Message:
GPS location has not been received
```

This is the same type of Alert exposed by the current `/operations/alerts` endpoint.

---

# Exception 2 — Missing Dock Assignment

The Operations logic also checks for a shipment that has reached a yard-related operational state but does not have a Dock assigned.

Conceptually:

```text
Delivery status = arrived / unloading
        +
dock_id missing
        ↓
Shipment Exception
```

This connects the Operations module with Dock Operations.

A frontend/operator can respond by obtaining a recommendation and assigning a Dock.

```text
Shipment Exception
      ↓
No Dock Assigned
      ↓
GET /dock-operations/recommend/{delivery_id}
      ↓
POST /dock-operations/assign/{delivery_id}
```

---

# Exception Side Effect

When an exception is detected, the Delivery is marked using:

```text
exception_detected = true
```

This indicates that the Delivery has already been identified by the exception-detection workflow.

---

# Duplicate Exception Protection

The backend uses the exception flag to prevent the same Delivery from repeatedly generating the same new exception detection.

Conceptually:

```text
Check Delivery
      ↓
exception_detected?
      │
      ├── true → Already detected
      │
      └── false
             ↓
       Evaluate conditions
             ↓
       Exception found
             ↓
       exception_detected = true
             ↓
          Create Alert
```

---

# Get Alerts

## `GET /operations/alerts`

Returns the Alerts stored by the Operations module.

### Example Request

```http
GET /operations/alerts
```

### Example Response

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

The `delivery_id` allows the frontend or another service to connect the Alert back to the affected shipment.

---

# Alert-to-Delivery Relationship

```text
Alert
  │
  │ delivery_id
  ▼
Delivery
```

For example:

```json
{
  "id": 1,
  "delivery_id": 2,
  "title": "Shipment Exception"
}
```

means that Alert `1` belongs to Delivery `2`.

The frontend can use that ID to open the appropriate shipment detail screen.

---

# Resolve Alert

## `PUT /operations/alerts/{alert_id}/resolve`

Marks an existing Alert as resolved.

### Path Parameter

| Parameter  | Type    | Required | Description       |
| ---------- | ------- | -------: | ----------------- |
| `alert_id` | integer |      Yes | Alert database ID |

### Example Request

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
Return success
```

---

# Successful Response

The endpoint returns a success response confirming that the Alert has been resolved.

Conceptually:

```json
{
  "message": "Alert resolved successfully"
}
```

After resolution:

```text
alert.resolved = true
```

---

# Important Resolution Behavior

Resolving an Alert changes the **Alert's resolved state**.

It should not be interpreted as automatically fixing the underlying shipment problem.

For example:

```text
GPS Missing
    ↓
Alert Created
    ↓
Operator resolves Alert
    ↓
alert.resolved = true
```

This does not itself provide new GPS coordinates.

Likewise:

```text
Dock Missing
    ↓
Alert Created
    ↓
Resolve Alert
```

does not itself assign a Dock.

The appropriate operational API must still be used to correct the underlying condition.

---

# How Operations Connects to Tracking

Tracking provides shipment GPS state.

Operations uses that state to detect abnormalities.

```text
Tracking
   ↓
Delivery GPS Information
   ↓
Operations
   ↓
Missing GPS?
   ↓
Exception Alert
```

Therefore GPS/tracking information affects operational monitoring.

---

# How Operations Connects to Dock Operations

Dock Operations manages shipment-to-dock assignment.

Operations can identify cases where the assignment is missing.

```text
Delivery Arrives
      ↓
dock_id?
  │
  ├── Present → Normal
  │
  └── Missing
         ↓
      Exception
         ↓
        Alert
         ↓
 Dock Recommendation
         ↓
 Dock Assignment
```

---

# How Operations Connects to Dashboard

Alerts can be displayed as part of the operations/dashboard UI.

A frontend can combine:

```http
GET /operations/alerts
```

with:

```http
GET /dashboard/summary
```

and shipment information to build an operations-control screen.

Conceptually:

```text
Dashboard
   │
   ├── Shipment KPIs
   ├── Dock Status
   ├── Live Shipments
   └── Operational Alerts
```

---

# Frontend Integration

A frontend Alerts panel can use:

```text
Page Load / Poll
      ↓
GET /operations/alerts
      ↓
Render Alert Cards
```

Example:

```text
CRITICAL

Shipment Exception
GPS location has not been received

Delivery #2

[View Shipment] [Resolve]
```

Selecting **View Shipment** can use `delivery_id` to open the Delivery/tracking screen.

Selecting **Resolve** calls:

```http
PUT /operations/alerts/{alert_id}/resolve
```

---

# Detection Integration

The detection endpoints can be invoked to run the current detection logic:

```text
POST /operations/detect-delays
           ↓
Detect overdue shipments

POST /operations/detect-exceptions
           ↓
Detect abnormal shipment states
```

The frontend does not need to reproduce these detection rules.

The detection logic remains inside the E2 backend.

---

# Cross-Team Integration

Another service only needs to understand:

```text
Run Detection
      ↓
Read Alerts
      ↓
Use delivery_id
      ↓
Handle underlying shipment
      ↓
Resolve Alert
```

For example:

```text
Other Operations Service
        ↓
GET /operations/alerts
        ↓
Alert.delivery_id
        ↓
GET /tracking/shipment/id/{delivery_id}
```

No knowledge of the Python implementation is required.

---

# Error Handling

Integrating applications should handle:

| HTTP Status | Meaning                                     |
| ----------: | ------------------------------------------- |
|       `200` | Detection/read/resolve operation successful |
|       `404` | Alert does not exist when resolving         |
|       `422` | Invalid Alert ID/path validation            |
|       `500` | Unexpected backend processing failure       |

FastAPI errors normally use:

```json
{
  "detail": "Error message"
}
```

---

# Current Limitations

The current Operations API provides rule-based operational detection.

It does not currently provide:

* Predictive ML-based exception detection
* External notification delivery such as email/SMS
* Push notifications
* WebSocket alert streaming
* Automatic remediation of the underlying issue
* Authentication/authorization

An Alert should therefore be understood as:

```text
Problem Detected
      ↓
Operational Notification
      ↓
Human / Other Service Takes Action
```

rather than an automatic repair mechanism.

The core relationship is:

```text
Tracking + Delivery + Dock State
              ↓
          Operations
              ↓
            Alert
              ↓
      Operator / Frontend
```
