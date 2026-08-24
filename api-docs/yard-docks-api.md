# Yard Docks API

The Yard Docks API manages loading/unloading docks available inside the yard.

Dock records are later used by the **Delivery** and **Dock Operations** modules for dock recommendation, assignment, reassignment, and operational status tracking.

**Base path:** `/yard-docks`

---

## Endpoints

| Method | Endpoint                | Purpose            |
| ------ | ----------------------- | ------------------ |
| POST   | `/yard-docks/`          | Create a Yard Dock |
| GET    | `/yard-docks/`          | Get all Yard Docks |
| GET    | `/yard-docks/{dock_id}` | Get one Yard Dock  |
| PUT    | `/yard-docks/{dock_id}` | Update Dock status |
| DELETE | `/yard-docks/{dock_id}` | Delete a Yard Dock |

---

# Yard Dock Object

A Yard Dock stores information about a physical dock and its capabilities.

The model contains information such as:

| Field                    | Type          | Description                                |
| ------------------------ | ------------- | ------------------------------------------ |
| `id`                     | integer       | Database-generated Dock ID                 |
| `yard_name`              | string        | Yard containing the dock                   |
| `dock_number`            | string        | Dock identifier/number                     |
| `status`                 | string        | Current operational status                 |
| `dock_type`              | string / null | Type of dock                               |
| `supported_vehicle_type` | string / null | Supported vehicle type                     |
| `max_vehicle_length`     | float / null  | Maximum supported vehicle length           |
| `refrigerated`           | boolean       | Whether refrigeration support is available |
| `hazardous_allowed`      | boolean       | Whether hazardous loads are allowed        |

These capability fields can also be used by dock recommendation logic.

---

# Create Yard Dock

## `POST /yard-docks/`

Creates a new Yard Dock.

### Request

**Content-Type:** `application/json`

Example:

```json
{
  "yard_name": "Main Yard",
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

# Successful Response

**HTTP 201**

The backend stores the Yard Dock and returns the created record.

Example structure:

```json
{
  "id": 1,
  "yard_name": "Main Yard",
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

# Get All Yard Docks

## `GET /yard-docks/`

Returns all Yard Dock records.

### Example Request

```http
GET /yard-docks/
```

### Example Response

```json
[
  {
    "id": 1,
    "yard_name": "Main Yard",
    "dock_number": "D-01",
    "status": "available",
    "dock_type": "standard"
  },
  {
    "id": 2,
    "yard_name": "Main Yard",
    "dock_number": "D-02",
    "status": "reserved",
    "dock_type": "standard"
  }
]
```

The actual response follows the Yard Dock response schema.

The current endpoint does not implement pagination, filtering, or search.

---

# Get Yard Dock by ID

## `GET /yard-docks/{dock_id}`

Returns one Yard Dock.

### Path Parameter

| Parameter | Type    | Required | Description           |
| --------- | ------- | -------: | --------------------- |
| `dock_id` | integer |      Yes | Yard Dock database ID |

Example:

```http
GET /yard-docks/1
```

---

## Yard Dock Not Found

**HTTP 404**

```json
{
  "detail": "Yard/Dock not found"
}
```

---

# Update Yard Dock Status

## `PUT /yard-docks/{dock_id}`

Updates the operational status of an existing Yard Dock.

The current endpoint updates **status**, rather than acting as a complete edit endpoint for all Dock fields.

### Path Parameter

| Parameter | Type    | Required |
| --------- | ------- | -------: |
| `dock_id` | integer |      Yes |

### Query Parameter

| Parameter | Type   | Required |
| --------- | ------ | -------: |
| `status`  | string |      Yes |

Example:

```http
PUT /yard-docks/1?status=maintenance
```

---

# Supported Dock Status Values

The current backend accepts:

```text
available
occupied
reserved
maintenance
blocked
```

The supplied value is trimmed and converted to lowercase before validation.

For example:

```text
"AVAILABLE"
     ↓
"available"
```

---

# Meaning of Dock Statuses

### `available`

The Dock is available for assignment.

### `reserved`

The Dock has been assigned/reserved for a Delivery.

### `occupied`

The Dock is currently occupied.

### `maintenance`

The Dock is unavailable because of maintenance.

### `blocked`

The Dock is unavailable for operational use.

---

# Backend Logic

```text
Receive dock_id + status
        ↓
Find Yard Dock
        ↓
Dock exists?
 No → HTTP 404
        ↓ Yes
Normalize status
        ↓
Status allowed?
 No → HTTP 400
        ↓ Yes
Update status
        ↓
Commit
        ↓
Return updated Dock
```

---

# Invalid Status

If the supplied status is outside the supported values, the backend returns HTTP `400`.

The frontend should therefore use the known status values rather than allowing arbitrary text.

A dropdown/select control is suitable:

```text
Available
Reserved
Occupied
Maintenance
Blocked
```

---

# Delete Yard Dock

## `DELETE /yard-docks/{dock_id}`

Deletes an existing Yard Dock.

### Example Request

```http
DELETE /yard-docks/1
```

Before deletion, the backend checks the Dock's current operational state.

---

# Occupied Dock Protection

A Dock whose status is:

```text
occupied
```

cannot be deleted.

The backend returns:

**HTTP 400**

```json
{
  "detail": "Cannot delete an occupied dock"
}
```

This prevents an actively occupied Dock from being removed through the API.

---

# Successful Delete

If the Dock exists and is not occupied:

```json
{
  "message": "Yard/Dock deleted successfully"
}
```

---

# How Yard Docks Connect to Deliveries

A Delivery can reference a Yard Dock through:

```text
delivery.dock_id
```

Relationship:

```text
Yard Dock
    ↑
    │ dock_id
    │
Delivery
```

A Delivery does not necessarily need a Dock when it is first created.

For example:

```text
Delivery Created
      ↓
dock_id = null
      ↓
Shipment travels
      ↓
Dock recommendation
      ↓
Dock assignment
      ↓
delivery.dock_id = selected dock
```

This allows Dock assignment to happen later in the shipment lifecycle.

---

# Dock Operations Integration

The Yard Docks API manages the Dock records themselves.

The separate Dock Operations API handles operational decisions involving those Docks.

```text
Yard Docks API
      ↓
Stores Dock Information
      ↓
Dock Operations
      ├── Recommendation
      ├── Assignment
      └── Reassignment
```

Recommendation:

```http
GET /dock-operations/recommend/{delivery_id}
```

Assignment:

```http
POST /dock-operations/assign/{delivery_id}
```

Reassignment:

```http
POST /dock-operations/reassign/{delivery_id}
```

See `dock-operations-api.md` for those operations.

---

# Dock Recommendation Relationship

The currently registered recommendation logic considers Yard Dock information when ranking Docks.

Examples of information used by the current scoring logic include:

```text
status
supported_vehicle_type
refrigerated
dock_type
```

Therefore Yard Dock configuration directly affects recommendation results.

---

# Dock Assignment Side Effect

When a Dock is assigned through Dock Operations, the selected Dock is changed to:

```text
reserved
```

and the Delivery receives:

```text
dock_id = selected dock ID
```

Conceptually:

```text
Available Dock
      +
Delivery
      ↓
Dock Assignment
      ↓
Dock.status = reserved
      +
Delivery.dock_id = Dock.id
```

---

# Dock Reassignment

If a Delivery is moved to another Dock through the Dock Operations API:

```text
Old Dock
   ↓
available

New Dock
   ↓
reserved

Delivery
   ↓
dock_id = New Dock ID
```

This logic is handled by Dock Operations rather than by this Yard Docks API.

---

# Dashboard Integration

Dock information is also exposed through:

```http
GET /dashboard/dock-status
```

The Dashboard uses Yard Dock data to provide frontend-friendly Dock status information.

Dashboard summary also counts Dock states such as:

```text
total
available
occupied
reserved
```

Therefore a frontend dashboard does not need to manually calculate every Dock KPI from `/yard-docks/`.

---

# Frontend Integration

A Yard Management screen can load:

```text
Page Load
   ↓
GET /yard-docks/
   ↓
Render Dock Cards
```

For example:

```text
D-01
AVAILABLE

D-02
RESERVED

D-03
OCCUPIED

D-04
MAINTENANCE
```

Status can then determine how each Dock is displayed or whether it can be selected for an operation.

---

# Creating a Dock

Typical UI flow:

```text
Add Dock
   ↓
Enter Yard Information
   ↓
Enter Dock Capabilities
   ↓
POST /yard-docks/
   ↓
Dock Created
   ↓
Refresh Yard View
```

---

# Updating Dock Status

```text
Operator changes status
        ↓
PUT /yard-docks/{dock_id}?status=...
        ↓
Backend validates status
        ↓
Dock updated
        ↓
Refresh Dock card
```

---

# Cross-Team Integration Notes

Another application does not need to understand the Python Dock model.

It primarily needs to understand:

```text
Dock ID
Dock Status
Dock Capabilities
```

and the supported status values:

```text
available
occupied
reserved
maintenance
blocked
```

When another service needs to assign a Dock to a Delivery, it should normally use the **Dock Operations API**, rather than manually changing `delivery.dock_id`.

---

# Error Handling

| HTTP Status | Meaning                                               |
| ----------: | ----------------------------------------------------- |
|       `200` | Successful read/update/delete                         |
|       `201` | Yard Dock created                                     |
|       `400` | Invalid Dock status or occupied Dock deletion attempt |
|       `404` | Yard Dock not found                                   |
|       `422` | Request/path/query validation failure                 |

FastAPI HTTP errors normally use:

```json
{
  "detail": "Error message"
}
```

---

# Current Limitations

The current Yard Docks API does not implement:

* Pagination
* Search/filtering
* Full Dock-detail update through this route
* Authentication/authorization
* Automatic Dock occupancy sensing

Dock recommendation and assignment are handled separately by the **Dock Operations API**.

The frontend should therefore treat:

```text
/yard-docks
```

as Dock master/status management, and:

```text
/dock-operations
```

as the operational recommendation and assignment layer.
