# Integrations API

The Integrations API allows external backend systems such as **PR2** to send shipment information into the E2 backend.

The purpose of this API is to keep PR2 and E2 databases separate while still allowing both systems to exchange shipment data through REST.

---

## Base Path

```text
/integrations
```

---

# 1. Import Shipment from PR2

## Endpoint

```http
POST /integrations/shipments
```

## Purpose

Creates a new shipment inside E2 using shipment information received from an external system such as PR2.

The endpoint creates:

```text
PR2 Shipment Payload
        ↓
Shipment Integration Record
        ↓
Restock Order
        ↓
Delivery
        ↓
E2 Tracking / ETA / Yard / Dock Workflow
```

PR2 does not need direct access to the E2 PostgreSQL database.

---

## Request Body

```json
{
  "external_order_id": "PO-PR2-TEST-001",
  "tracking_number": "TRK-PR2-TEST-001",
  "trailer_id": "TRL-PR2-001",
  "shipment_reference": "SHIP-PR2-001",
  "carrier": "BlueDart",
  "quantity": 50,
  "scheduled_arrival": "2026-08-27T18:00:00",
  "destination_latitude": 23.0225,
  "destination_longitude": 72.5714,
  "source_system": "PR2"
}
```

---

## Request Fields

| Field | Type | Required | Description |
|---|---|---:|---|
| `external_order_id` | string | Yes | External order identifier from PR2 or another source system |
| `tracking_number` | string | Yes | Shipment tracking number |
| `trailer_id` | string / null | No | Trailer or truck identifier |
| `shipment_reference` | string / null | No | External shipment reference |
| `carrier` | string / null | No | Logistics carrier name |
| `quantity` | integer | Yes | Quantity associated with the incoming shipment |
| `scheduled_arrival` | datetime / null | No | Planned shipment arrival time |
| `destination_latitude` | number / null | No | Destination latitude |
| `destination_longitude` | number / null | No | Destination longitude |
| `source_system` | string | No | Source backend name; default is `PR2` |

---

## Successful Response

### Status

```http
201 Created
```

### Example Response

```json
{
  "message": "Shipment imported successfully into E2",
  "integration_id": 1,
  "delivery_id": 4,
  "restock_order_id": 3,
  "external_order_id": "PO-PR2-TEST-001",
  "tracking_number": "TRK-PR2-TEST-001",
  "trailer_id": "TRL-PR2-001",
  "shipment_reference": "SHIP-PR2-001",
  "status": "scheduled",
  "source_system": "PR2"
}
```

---

## Response Fields

| Field | Type | Description |
|---|---|---|
| `message` | string | Import status message |
| `integration_id` | integer | E2 shipment integration record ID |
| `delivery_id` | integer | E2 delivery ID created for the shipment |
| `restock_order_id` | integer | E2 restock order created for the shipment |
| `external_order_id` | string | External PR2 order ID |
| `tracking_number` | string | Shipment tracking number |
| `trailer_id` | string / null | Trailer identifier |
| `shipment_reference` | string / null | Shipment reference |
| `status` | string | Initial E2 delivery status |
| `source_system` | string | External source system |

---

# Internal Processing

When a valid request is received, E2 performs the following operations.

## Step 1 — Validate Quantity

The shipment quantity must be greater than zero.

Invalid example:

```json
{
  "quantity": 0
}
```

This results in:

```http
400 Bad Request
```

---

## Step 2 — Check External Order Duplicate

E2 checks whether the supplied:

```text
external_order_id
```

already exists inside:

```text
shipment_integrations
```

This prevents the same PR2 order from being imported more than once.

If the external order already exists, E2 returns:

```http
409 Conflict
```

Example error:

```json
{
  "detail": {
    "message": "This external order has already been imported into E2",
    "external_order_id": "PO-PR2-TEST-001",
    "existing_delivery_id": 4
  }
}
```

---

## Step 3 — Check Tracking Number Duplicate

E2 checks whether the tracking number already belongs to another delivery.

If the tracking number already exists:

```http
409 Conflict
```

Example:

```json
{
  "detail": {
    "message": "Tracking number already exists in E2",
    "tracking_number": "TRK-PR2-TEST-001",
    "existing_delivery_id": 4
  }
}
```

---

## Step 4 — Create or Reuse Integration Product

E2 uses a generic integration product:

```text
SKU: PR2-INTEGRATION
Name: PR2 Imported Shipment
Category: integration
```

If it does not exist, the backend creates it automatically.

---

## Step 5 — Create or Reuse Integration Supplier

E2 uses:

```text
PR2 Integration Supplier
```

for shipment-import records when no direct E2 supplier mapping exists.

If it does not already exist, the backend creates it.

---

## Step 6 — Create Restock Order

E2 creates a `RestockOrder` using the shipment quantity and scheduled arrival.

Conceptually:

```text
Integration Product
        +
Integration Supplier
        +
Quantity
        ↓
Restock Order
```

---

## Step 7 — Create Delivery

E2 creates a new `Delivery` linked to the restock order.

Initial shipment state:

```text
scheduled
```

The delivery can contain:

```text
Tracking Number
Trailer ID
Shipment Reference
Carrier
Scheduled Arrival
Destination GPS
```

---

## Step 8 — Create Integration Mapping

E2 stores the relationship between the external order and the new E2 delivery in:

```text
shipment_integrations
```

Example relationship:

```text
PR2 Order
PO-PR2-TEST-001
        ↓
ShipmentIntegration
        ↓
E2 Delivery
ID = 4
```

---

# Database Mapping

The integration flow uses the following E2 tables:

```text
shipment_integrations
restock_orders
deliveries
```

Supporting entities may also use:

```text
products
suppliers
```

The external PR2 database is not directly accessed by E2.

---

# PR2 → E2 Architecture

```text
┌─────────────────────────┐
│      PR2 Database       │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│      PR2 Backend        │
└────────────┬────────────┘
             │
             │ POST JSON
             ▼
┌─────────────────────────┐
│      E2 Backend         │
│ /integrations/shipments │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ shipment_integrations   │
└────────────┬────────────┘
             │
             ├──────────────► Restock Order
             │
             └──────────────► Delivery
                                │
                                ├── Tracking
                                ├── ETA
                                ├── Delay Detection
                                ├── Yard Operations
                                ├── Dock Scheduling
                                └── Dashboard
```

---

# Verifying an Imported Shipment

After shipment creation, the imported shipment can be verified using E2 tracking APIs.

## By Tracking Number

```http
GET /tracking/shipment/TRK-PR2-TEST-001
```

## By Trailer ID

```http
GET /tracking/trailer/TRL-PR2-001
```

## By Shipment Reference

```http
GET /tracking/reference/SHIP-PR2-001
```

All three should return the same E2 delivery.

---

# Example Imported Shipment

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
  "id": 4,
  "delay_detected": false,
  "exception_detected": false,
  "last_gps_update": null
}
```

---

# Error Responses

## 400 — Invalid Quantity

```json
{
  "detail": "Quantity must be greater than zero"
}
```

---

## 409 — External Order Already Imported

```json
{
  "detail": {
    "message": "This external order has already been imported into E2",
    "external_order_id": "PO-PR2-TEST-001",
    "existing_delivery_id": 4
  }
}
```

---

## 409 — Tracking Number Already Exists

```json
{
  "detail": {
    "message": "Tracking number already exists in E2",
    "tracking_number": "TRK-PR2-TEST-001",
    "existing_delivery_id": 4
  }
}
```

---

## 422 — Validation Error

FastAPI automatically returns `422 Unprocessable Entity` if required request fields are missing or have invalid types.

Example:

```json
{
  "detail": [
    {
      "loc": [
        "body",
        "tracking_number"
      ],
      "msg": "Field required",
      "type": "missing"
    }
  ]
}
```

---

## 500 — Import Failure

If the database transaction fails unexpectedly:

```json
{
  "detail": "Failed to import shipment into E2"
}
```

---

# Integration Contract for PR2 Team

The PR2 backend only needs:

```text
HTTP Method:
POST

Endpoint:
/integrations/shipments

Content-Type:
application/json
```

PR2 does **not** need:

```text
E2 PostgreSQL credentials
E2 database access
E2 table access
E2 internal SQLAlchemy models
```

PR2 only needs to send a valid JSON request using the defined API contract.

---

# Local Development URL

```text
http://127.0.0.1:8000/integrations/shipments
```

This URL works only on the machine running E2 locally.

---

# Production URL

After E2 deployment, PR2 should call:

```text
https://YOUR-E2-BACKEND-DOMAIN/integrations/shipments
```

The deployed URL should be added here after production deployment.

---

# Swagger

Local Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Navigate to:

```text
Integrations
    ↓
POST /integrations/shipments
```

---

# Summary

The Integrations API provides a clean service-to-service boundary between PR2 and E2.

```text
PR2 owns procurement/order data.

E2 owns shipment tracking,
ETA,
yard operations,
dock scheduling,
alerts,
and operational dashboards.
```

The two systems remain independently deployable and communicate through REST instead of sharing one database.
