# Dashboard API

The Dashboard API provides aggregated operational data for the E2 frontend.

**Base path:** `/dashboard`

---

## Endpoints

| Method | Endpoint                    | Purpose                             |
| ------ | --------------------------- | ----------------------------------- |
| GET    | `/dashboard/summary`        | Get overall operational KPIs        |
| GET    | `/dashboard/live-shipments` | Get active shipment information     |
| GET    | `/dashboard/dock-status`    | Get current Yard Dock status        |
| GET    | `/dashboard/insights`       | Get rule-based operational insights |

---

# 1. Dashboard Summary

## `GET /dashboard/summary`

Returns the main operational statistics required by the dashboard.

No request body or query parameters are required.

### Example Request

```http
GET /dashboard/summary
```

### Response

```json
{
  "shipments": {
    "total": 10,
    "active": 5,
    "delivered": 3,
    "delayed": 2,
    "exceptions": 1
  },
  "docks": {
    "total": 6,
    "available": 2,
    "occupied": 2,
    "reserved": 2
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

The values above are examples. Actual values are calculated from the database.

---

## Shipment Calculations

### Total

Counts all Delivery records.

### Active

A Delivery is considered active when its status is:

```text
scheduled
in_transit
delayed
arrived
unloading
```

### Delivered

Counts Deliveries where:

```text
status == "delivered"
```

### Delayed

Counts Deliveries where:

```text
delay_detected == true
```

### Exceptions

Counts Deliveries where:

```text
exception_detected == true
```

---

## Dock Calculations

The response provides:

```text
total
available
occupied
reserved
```

`total` includes every Yard Dock.

The remaining values count Docks with the corresponding status.

---

## Inventory Calculations

### Low Stock

An Inventory item is considered low stock when:

```text
inventory.current_stock <= product.reorder_level
```

The current calculation uses `current_stock` directly.

### Pending Restock Orders

Counts Restock Orders where:

```text
status == "pending"
```

---

## Active Alerts

Counts Alerts where:

```text
resolved == false
```

---

# 2. Live Shipments

## `GET /dashboard/live-shipments`

Returns Deliveries currently considered active.

### Example Request

```http
GET /dashboard/live-shipments
```

### Active Statuses

```text
scheduled
in_transit
delayed
arrived
unloading
```

### Response Fields

| Field                | Type            | Description       |
| -------------------- | --------------- | ----------------- |
| `id`                 | integer         | Delivery ID       |
| `tracking_number`    | string / null   | Tracking number   |
| `carrier`            | string / null   | Carrier           |
| `status`             | string          | Delivery status   |
| `latitude`           | float / null    | Current latitude  |
| `longitude`          | float / null    | Current longitude |
| `location`           | string / null   | Current location  |
| `eta_minutes`        | integer / null  | Remaining ETA     |
| `estimated_arrival`  | datetime / null | Estimated arrival |
| `delay_detected`     | boolean         | Delay flag        |
| `exception_detected` | boolean         | Exception flag    |

### Example Response

```json
[
  {
    "id": 2,
    "tracking_number": "TRK-10001",
    "carrier": "ABC Logistics",
    "status": "in_transit",
    "latitude": 22.5726,
    "longitude": 88.3639,
    "location": "Kolkata",
    "eta_minutes": 120,
    "estimated_arrival": "2026-08-25T03:00:00",
    "delay_detected": false,
    "exception_detected": false
  }
]
```

### Frontend Usage

This endpoint can drive:

* Live shipment map
* Active shipment table
* Shipment status indicators
* ETA display
* Delay/exception indicators

Since the backend currently does not use WebSockets, the frontend can poll this endpoint for updated shipment positions.

Latitude and longitude may be `null`, so the frontend should check coordinates before displaying a map marker.

---

# 3. Dock Status

## `GET /dashboard/dock-status`

Returns the current state of all Yard Docks.

### Example Request

```http
GET /dashboard/dock-status
```

### Response Fields

| Field               | Type          | Description               |
| ------------------- | ------------- | ------------------------- |
| `id`                | integer       | Dock ID                   |
| `yard_name`         | string        | Yard name                 |
| `dock_number`       | string        | Dock number               |
| `status`            | string        | Current Dock status       |
| `dock_type`         | string / null | Dock type                 |
| `refrigerated`      | boolean       | Refrigeration capability  |
| `hazardous_allowed` | boolean       | Hazardous-load capability |

### Example Response

```json
[
  {
    "id": 1,
    "yard_name": "Main Yard",
    "dock_number": "D-01",
    "status": "available",
    "dock_type": "standard",
    "refrigerated": false,
    "hazardous_allowed": false
  },
  {
    "id": 2,
    "yard_name": "Main Yard",
    "dock_number": "D-02",
    "status": "reserved",
    "dock_type": "standard",
    "refrigerated": true,
    "hazardous_allowed": false
  }
]
```

### Frontend Usage

This endpoint can directly drive a Yard/Dock status board.

```text
GET /dashboard/dock-status
        ↓
Dock Cards
        ↓
Available / Reserved / Occupied / etc.
```

For modifying or assigning Docks, use the dedicated Yard Dock and Dock Operations APIs.

---

# 4. Operational Insights

## `GET /dashboard/insights`

Returns human-readable operational insights calculated from current backend data.

These insights are **rule-based**, not generated by the ML model.

### Example Request

```http
GET /dashboard/insights
```

### Response

```json
{
  "insights": [
    {
      "type": "delay",
      "priority": "high",
      "message": "2 shipment(s) are delayed. Review ETA and dock allocation."
    }
  ],
  "count": 1
}
```

---

## Delay Insight

If Deliveries exist where:

```text
delay_detected == true
```

the backend generates a high-priority delay insight.

---

## No Available Docks

If:

```text
available docks == 0
```

the backend generates a high-priority dock-capacity insight.

---

## Low Dock Availability

If available Docks are greater than zero but:

```text
available docks <= 2
```

the backend generates a medium-priority dock-capacity insight.

---

## Unresolved Alerts

If Alerts exist where:

```text
resolved == false
```

the backend generates a high-priority alert insight.

---

## Normal Operations

If no operational issue produces an insight, the backend returns a low-priority system message indicating that operations are running normally.

---

# Dashboard Data Flow

```text
Deliveries ─────────┐
Yard Docks ─────────┤
Inventory ──────────┤
Products ───────────┼──→ Dashboard API
Restock Orders ─────┤
Alerts ─────────────┘
                    ↓
              Aggregated Data
                    ↓
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
Live Shipment Map / Table

GET /dashboard/dock-status
        ↓
Yard Dock Board

GET /dashboard/insights
        ↓
Operational Insights
```

The frontend should consume these calculated results instead of recreating the aggregation rules.

---

# Error Handling

No matching database records are normal conditions.

For example, no active shipments can return:

```json
[]
```

and summary counters can return `0`.

Unexpected backend/database failures may result in HTTP `500`.

---

# Current Limitations

The Dashboard API currently does not implement:

* Date-range filtering
* Historical analytics
* Time-series data
* Yard-specific filtering
* Supplier-specific filtering
* Pagination
* WebSocket/SSE updates
* Authentication/authorization

The `/dashboard/insights` endpoint is rule-based and should not be presented as an ML/AI prediction system.
