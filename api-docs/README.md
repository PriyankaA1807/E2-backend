# E2 Backend API Documentation

API documentation for the **E2 Smart Restock & Yard Dock Delivery Tracker**.

E2 provides APIs for inventory/restock management, shipment integration, live shipment tracking, GPS simulation, ETA prediction, yard and dock operations, operational monitoring, and dashboard visibility.

---

# Base URL

## Local Development

```text
http://127.0.0.1:8000
```

After deployment, replace the local URL with the deployed backend URL.

Example:

```text
https://<deployed-e2-backend>
```

---

# Interactive API Documentation

FastAPI automatically provides Swagger UI at:

```text
http://127.0.0.1:8000/docs
```

and OpenAPI schema at:

```text
http://127.0.0.1:8000/openapi.json
```

After deployment:

```text
https://<deployed-e2-backend>/docs
```

This allows frontend and other backend teams to test E2 APIs directly.

---

# API Modules

| Module | Documentation | Main Responsibility |
|---|---|---|
| Products | [products-api.md](products-api.md) | Product master data |
| Inventory | [inventory-api.md](inventory-api.md) | Stock management |
| Suppliers | [suppliers-api.md](suppliers-api.md) | Supplier management |
| Restock Orders | [restock-orders-api.md](restock-orders-api.md) | Restocking workflow |
| Deliveries | [deliveries-api.md](deliveries-api.md) | Shipment/Delivery records |
| Integrations | [integrations-api.md](integrations-api.md) | External/PR2 shipment ingestion |
| Tracking | [tracking-api.md](tracking-api.md) | Shipment tracking and history |
| ETA Prediction | [eta-api.md](eta-api.md) | ML-based ETA prediction |
| GPS Simulation | [simulation-api.md](simulation-api.md) | GPS movement and simulated WMS feed |
| Yard Docks | [yard-docks-api.md](yard-docks-api.md) | Dock configuration and status |
| Dock Operations | [dock-operations-api.md](dock-operations-api.md) | Recommendation, scheduling and assignment |
| Operations & Alerts | [operations-api.md](operations-api.md) | Delay, exception and dock issue detection |
| Dashboard | [dashboard-api.md](dashboard-api.md) | Frontend operational views and KPIs |

---

# Main Integration Endpoint

External systems such as **PR2** can send shipment information to E2 through:

```http
POST /integrations/shipments
```

Example architecture:

```text
PR2 / External Backend
          ↓
POST /integrations/shipments
          ↓
         E2
          ↓
Shipment Integration Record
          ↓
Restock Order
          ↓
Delivery
          ↓
Tracking / ETA / Yard / Dock Operations
```

See:

```text
integrations-api.md
```

for the complete integration contract.

---

# End-to-End E2 Flow

```text
Product
   ↓
Inventory
   ↓
Supplier
   ↓
Restock Order
   ↓
Delivery
   ↓
Tracking
   ↓
GPS / Shipment Movement
   ↓
ETA
   ↓
Delay & Exception Detection
   ↓
Yard Arrival
   ↓
Dock Recommendation
   ↓
Dock Scheduling
   ↓
Dock Assignment / Reassignment
   ↓
Operational Monitoring
   ↓
Dashboard
```

---

# Cross-Team Shipment Flow

For external shipment integration:

```text
PR2
 │
 │ Shipment Data
 ▼
POST /integrations/shipments
 │
 ▼
E2 Database
 │
 ├── Shipment Integration
 │
 ├── Restock Order
 │
 └── Delivery
       │
       ├── Tracking
       ├── GPS Simulation
       ├── ETA
       ├── Delay Detection
       ├── Yard Status
       ├── Dock Scheduling
       └── Dock Assignment
              │
              ▼
           Dashboard
```

---

# Shipment Identification

E2 supports multiple shipment identifiers.

Depending on the API, a shipment can be identified using:

```text
delivery_id
tracking_number
trailer_id
shipment_reference
```

Examples:

```http
GET /tracking/shipment/{tracking_number}
```

```http
GET /tracking/shipment/id/{delivery_id}
```

```http
GET /tracking/trailer/{trailer_id}
```

```http
GET /tracking/reference/{shipment_reference}
```

This allows different systems to use the identifier most relevant to their workflow.

---

# ETA Architecture

E2 currently supports two ETA mechanisms.

## ML ETA

Uses the trained:

```text
RandomForestRegressor
```

Conceptually:

```text
Distance
Quantity
Supplier Delay History
Carrier Delay History
        ↓
Random Forest
        ↓
Predicted Delivery Time
```

See:

```text
eta-api.md
```

---

## GPS / Movement ETA

During shipment simulation:

```text
Remaining Distance
        ÷
Current Speed
        ↓
Remaining Travel Time
        ↓
Estimated Arrival
```

The ML ETA and movement-based ETA are separate mechanisms.

---

# Yard and Dock Architecture

```text
Incoming Trailer
      ↓
Yard Status
      ↓
Dock Availability
      ↓
Dock Recommendation
      ↓
Dock Schedule
      ↓
Trailer-Door Allocation
      ↓
Assignment
      ↓
Reassignment if Required
```

The Yard Dock API manages dock records.

The Dock Operations API handles operational allocation decisions.

The Dashboard exposes frontend-friendly yard, schedule, and trailer-door views.

---

# Operational Monitoring

E2 can monitor conditions such as:

```text
Shipment Delay
Shipment Exception
Missing GPS
Dock Unavailable
Dock Reassignment Required
```

These conditions can generate operational alerts and dashboard insights.

See:

```text
operations-api.md
```

---

# Dashboard

The Dashboard API provides aggregated operational information for the frontend.

It can expose views such as:

```text
Operational Summary
Live Shipments
Dock Status
Yard Status
Dock Schedule
Trailer-Door Allocation
Operational Insights
```

See:

```text
dashboard-api.md
```

---

# Simulated WMS Feed

E2 provides a simulated WMS-style operational feed through:

```http
GET /simulation/wms-feed
```

It can expose:

```text
Trailers
+
Shipment State
+
Dock Assignment
+
Dock Capacity
```

This is useful for frontend development and cross-team integration testing without requiring a real external WMS.

---

# API Conventions

## API Versioning

The project currently does not use an:

```text
/api/v1
```

prefix.

Routes are exposed directly, for example:

```text
/deliveries
/tracking
/dashboard
/integrations
```

---

## Authentication

Authentication and authorization are not currently implemented.

The current APIs should therefore be treated as development/integration APIs.

---

## Error Format

FastAPI errors generally use:

```json
{
  "detail": "Error message"
}
```

Validation failures can return FastAPI's structured validation response.

---

# Common HTTP Status Codes

| Status | Meaning |
|---:|---|
| `200` | Successful request |
| `201` | Resource created successfully |
| `400` | Invalid operation/request |
| `404` | Requested resource not found |
| `409` | Conflict/duplicate resource when applicable |
| `422` | FastAPI request validation failure |
| `500` | Unexpected backend/server failure |

---

# Pagination

List endpoints currently do not generally implement pagination.

For example:

```http
GET /deliveries/
GET /yard-docks/
```

may return complete collections.

---

# Live Updates

The current backend uses HTTP-based updates/polling rather than WebSockets or Server-Sent Events.

A frontend can periodically request endpoints such as:

```http
GET /dashboard/live-shipments
```

```http
GET /dashboard/yard-status
```

```http
GET /dashboard/dock-status
```

to refresh operational state.

---

# Database

E2 uses PostgreSQL through SQLAlchemy.

Major tables include:

```text
products
inventory
suppliers
restock_orders
deliveries
tracking_events
yard_docks
alerts
shipment_integrations
```

External teams do not need direct database access.

They should communicate with E2 through the HTTP APIs.

---

# Machine Learning

The ETA prediction module uses:

```text
scikit-learn
RandomForestRegressor
```

The trained model is stored inside the E2 backend.

External applications do not need:

```text
Python
scikit-learn
.pkl model access
training code
```

They consume ETA predictions through the API.

---

# Technology Stack

```text
Python
FastAPI
SQLAlchemy
Pydantic
PostgreSQL
scikit-learn
Uvicorn
```

---

# Recommended Integration Strategy

Frontend applications and other backend services should treat E2 as an independent HTTP service.

```text
Frontend / PR2 / Other Service
             ↓
          HTTP API
             ↓
             E2
             ↓
     Business Logic + ML
             ↓
         PostgreSQL
```

Do not reproduce E2's internal scheduling, ETA, tracking, or dock-allocation logic in another service unless specifically required.

---

# Local Testing

Start the backend:

```bash
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000/docs
```

Swagger UI can be used to test the complete API.

---

# Deployment

After deployment, teams should use the deployed URL instead of:

```text
http://127.0.0.1:8000
```

For example:

```text
https://<e2-deployment-url>/integrations/shipments
```

The exact production URL should be added to this documentation after deployment.

---

# Documentation Purpose

These API documents are intended for:

- frontend developers;
- PR2/backend integration developers;
- other project teams;
- future maintainers;
- developers unfamiliar with the Python/FastAPI implementation.

An integrating developer should be able to understand the API contract without reading E2's internal Python implementation.

For detailed:

- request bodies;
- response structures;
- query/path parameters;
- validation;
- error handling;
- backend behavior;
- database effects;
- frontend usage;
- cross-team integration;

see the corresponding API documentation file in this directory.
