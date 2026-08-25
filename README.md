# E2 Backend

## Smart Restock & Yard Dock Delivery Tracker

E2 is a logistics, inventory-restocking, shipment-tracking, ETA-prediction, and yard/dock operations backend built using **FastAPI, PostgreSQL, SQLAlchemy, Pydantic, and Scikit-learn**.

The system connects procurement and restocking workflows with shipment execution, GPS tracking, machine-learning-based ETA prediction, delay and exception detection, dock scheduling, trailer-to-door allocation, operational dashboards, and external shipment integration.

E2 can also receive shipment information from another backend system such as **PR2** through a dedicated integration API.

The backend is deployed on **Render** and uses a managed **PostgreSQL database**.

---

# Table of Contents

1. Overview
2. Problem Statement
3. Solution
4. Key Features
5. Technology Stack
6. System Architecture
7. End-to-End Workflow
8. Project Structure
9. Database Architecture
10. API Architecture
11. System APIs
12. Products
13. Inventory
14. Suppliers
15. Restock Orders
16. Yard Docks
17. Deliveries
18. External Shipment Integration
19. Shipment Tracking
20. ETA Prediction
21. GPS Simulation
22. Dock Recommendation
23. Dock Operations
24. Delay Detection
25. Exception Detection
26. Alerts
27. Dashboard
28. Yard Status
29. Dock Scheduling
30. Trailer-Door Allocation
31. Background Processing
32. Installation & Setup
33. Environment Configuration
34. Running the Application
35. Swagger / OpenAPI
36. Testing
37. Frontend Integration
38. PR2 Integration
39. Design Decisions
40. Current Limitations
41. Future Improvements
42. Deployment
43. Project Status
44. Repository

---

# 1. Overview

E2 Backend is a logistics and inventory-management backend designed to manage the lifecycle of inventory replenishment and incoming shipments.

Instead of limiting the system to inventory CRUD operations, E2 connects procurement, logistics, shipment tracking, ETA prediction, yard management, and dock operations.

```text
Inventory
   ↓
Restock Requirement
   ↓
Supplier / Restock Order
   ↓
Shipment / Delivery
   ↓
Shipment Tracking
   ↓
GPS / ETA Monitoring
   ↓
Delay & Exception Detection
   ↓
Yard Arrival
   ↓
Dock Recommendation
   ↓
Dock Scheduling
   ↓
Trailer-Door Allocation
   ↓
Dock Assignment / Reassignment
   ↓
Arrival / Unloading
   ↓
Operational Dashboard
```

E2 also supports external shipment ingestion:

```text
External System / PR2
        ↓
POST /integrations/shipments
        ↓
E2 Integration Layer
        ↓
Restock Order + Delivery
        ↓
E2 Logistics Workflow
```

The backend exposes REST APIs that can be consumed by web applications, mobile applications, dashboards, and other backend services.

---

# 2. Problem Statement

Inventory replenishment involves more than simply creating a purchase order.

Once inventory reaches a reorder level, operations teams need visibility into:

- which product requires replenishment;
- which supplier is fulfilling the order;
- how much inventory is incoming;
- which shipment belongs to the order;
- where the shipment currently is;
- when the shipment is expected to arrive;
- whether the shipment is delayed;
- whether a tracking or operational exception has occurred;
- which trailer is carrying the shipment;
- which dock should receive the vehicle;
- whether the current dock assignment remains valid;
- when a dock is available;
- whether trailer reassignment is required;
- and which operational events require immediate attention.

When procurement, shipment tracking, ETA, yard operations, and dock scheduling are handled separately, operational visibility becomes fragmented.

E2 provides a unified backend for these workflows.

---

# 3. Solution

E2 combines:

```text
Inventory
+
Procurement
+
Supplier Management
+
Shipment Integration
+
Delivery Management
+
Tracking
+
GPS
+
Machine Learning ETA
+
Delay Detection
+
Exception Detection
+
Yard Operations
+
Dock Scheduling
+
Trailer-Door Allocation
+
Operational Alerts
+
Dashboard
```

The backend can:

- maintain product information;
- maintain inventory;
- manage suppliers;
- create and manage restock orders;
- receive shipments from external systems;
- create delivery records;
- track trailers and shipments;
- maintain shipment event history;
- simulate GPS movement;
- calculate distance remaining;
- calculate dynamic ETA;
- predict delivery time using a trained ML model;
- detect predicted shipment delays;
- detect operational exceptions;
- generate alerts;
- recommend suitable docks;
- assign and reassign docks;
- create dock schedules;
- evaluate trailer-door allocation;
- recommend reassignment when an assigned dock becomes unsuitable;
- expose operational dashboard information;
- automatically process simulated shipment movement.

---

# 4. Key Features

## Inventory & Procurement

- Product management
- Inventory tracking
- Reorder-level support
- Supplier management
- Restock-order management
- Incoming shipment association

## External Integration

- Dedicated shipment integration API
- External order ID support
- Source-system tracking
- Tracking-number ingestion
- Trailer ID ingestion
- Shipment-reference ingestion
- Automatic E2 delivery creation
- Integration audit record

## Logistics

- Delivery creation
- Unique shipment tracking
- Carrier information
- Trailer identification
- Shipment references
- Delivery status lifecycle
- Shipment lookup
- Tracking-event history

## Intelligent ETA

- Dynamic ETA calculation
- Machine-learning ETA prediction
- Trained Random Forest model
- Distance-based shipment features
- Quantity-aware prediction
- Supplier delay-history input
- Carrier delay-history input
- Predicted delay calculation
- Automatic delay-state update
- Delay alert creation

## GPS Simulation

- Start shipment simulation
- Incrementally update vehicle position
- Simulated vehicle speed
- Remaining-distance calculation
- Dynamic ETA updates
- Estimated-arrival updates
- Automatic arrival detection

## Yard & Dock Operations

- Yard/dock management
- Dock availability state
- Dock compatibility
- Dock recommendation
- Dock assignment
- Dock reassignment
- Automatic reassignment support
- Yard-status visibility

## Dock Scheduling

- Incoming trailer scheduling
- 30-minute operational slots
- Existing assignment preservation
- Dock compatibility scoring
- Minimal waiting-time selection
- Priority-aware scheduling
- Unscheduled shipment reporting

## Trailer-Door Allocation

- Current dock evaluation
- Recommended dock comparison
- Reassignment detection
- Allocation status
- Delayed trailer visibility

## Operational Intelligence

- Delay detection
- Shipment-exception detection
- Operational alerts
- Alert resolution
- Live shipment monitoring
- Yard monitoring
- Dock monitoring
- Dashboard summaries
- Operational insights

## Automation

- Background shipment tracking
- Automatic GPS movement
- Automatic ETA recalculation
- Automatic arrival processing

---

# 5. Technology Stack

| Layer | Technology |
|---|---|
| Language | Python |
| API Framework | FastAPI |
| ASGI Server | Uvicorn |
| ORM | SQLAlchemy |
| Database | PostgreSQL |
| Validation | Pydantic |
| Data Processing | Pandas / NumPy |
| Machine Learning | Scikit-learn |
| ETA Model | RandomForestRegressor |
| Model Serialization | Joblib |
| API Documentation | OpenAPI / Swagger |
| Configuration | Environment Variables / `.env` |
| Deployment | Render |
| Production Database | Render PostgreSQL |
| Version Control | Git / GitHub |

---

# 6. System Architecture

```text
                    ┌─────────────────────┐
                    │      Frontend       │
                    └──────────┬──────────┘
                               │
                           REST / JSON
                               │
                    ┌──────────▼──────────┐
                    │      FastAPI        │
                    │    Application      │
                    └──────────┬──────────┘
                               │
       ┌───────────────────────┼───────────────────────┐
       │                       │                       │
       ▼                       ▼                       ▼
┌──────────────┐      ┌─────────────────┐     ┌─────────────────┐
│ Inventory &  │      │ Logistics &     │     │ Yard / Dock     │
│ Procurement  │      │ Tracking        │     │ Operations      │
└──────┬───────┘      └────────┬────────┘     └────────┬────────┘
       │                       │                       │
       └───────────────────────┼───────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │     SQLAlchemy      │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │     PostgreSQL      │
                    └─────────────────────┘
```

External system integration:

```text
External Backend / PR2
          │
          │ HTTP / JSON
          ▼
┌─────────────────────────┐
│ POST                    │
│ /integrations/shipments │
└────────────┬────────────┘
             │
             ├── ShipmentIntegration
             ├── RestockOrder
             └── Delivery
```

Additional processing:

```text
┌─────────────────────┐
│ ML / ETA            │
│ Random Forest       │
└─────────────────────┘

┌─────────────────────┐
│ Background Tracking │
│ Loop                │
└─────────────────────┘
```

Production architecture:

```text
GitHub Repository
        ↓
Render Web Service
        ↓
FastAPI + Uvicorn
        ↓
SQLAlchemy
        ↓
Render PostgreSQL
```

---

# 7. End-to-End Workflow

## Step 1 — Product

A product is registered.

Typical fields include:

```text
SKU
Name
Category
Unit Price
Reorder Level
```

## Step 2 — Inventory

Inventory is associated with the product.

```text
Product
   ↓
Current Stock
Reserved Stock
```

## Step 3 — Supplier

Supplier information is stored for procurement operations.

## Step 4 — Restock Order

A restock order connects:

```text
Product + Supplier + Quantity
```

## Step 5 — Shipment / Delivery

A shipment is created against the restock order.

Alternatively, an external backend can send shipment information through:

```http
POST /integrations/shipments
```

## Step 6 — Tracking

Shipment events can be recorded and queried using tracking number, delivery ID, trailer ID, or shipment reference.

## Step 7 — ETA

The system calculates and predicts arrival time.

## Step 8 — GPS Simulation

For development and demonstration, shipment movement can be simulated.

```text
GPS
 ↓
Distance Remaining
 ↓
Speed
 ↓
ETA
 ↓
Estimated Arrival
```

## Step 9 — Delay / Exception Detection

Shipment state is evaluated for delays or abnormal operational conditions.

## Step 10 — Yard Arrival

Incoming trailers become visible to yard operations.

## Step 11 — Dock Recommendation

Suitable docks are ranked according to operational compatibility.

## Step 12 — Dock Scheduling

Incoming trailers receive dock time windows.

## Step 13 — Trailer-Door Allocation

Current assignments are compared with recommended schedules.

## Step 14 — Assignment / Reassignment

A dock can be assigned or changed when operational conditions require it.

## Step 15 — Dashboard

Operational state is exposed to the frontend through dashboard APIs.

---

# 8. Project Structure

```text
E2-backend/
│
├── app/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── background.py
│   │
│   ├── routers/
│   │   ├── products.py
│   │   ├── inventory.py
│   │   ├── suppliers.py
│   │   ├── restock_orders.py
│   │   ├── yard_docks.py
│   │   ├── deliveries.py
│   │   ├── tracking.py
│   │   ├── eta.py
│   │   ├── simulation.py
│   │   ├── dock_operations.py
│   │   ├── dock_recommendation.py
│   │   ├── operations.py
│   │   ├── dashboard.py
│   │   └── integrations.py
│   │
│   └── ml/
│       ├── eta.py
│       ├── eta_predictor.py
│       ├── train_eta_model.py
│       ├── dock_recommender.py
│       └── saved_models/
│           └── eta_model.pkl
│
├── api-docs/
├── requirements.txt
├── README.md
├── .gitignore
└── .env.example
```

---

# 9. Database Architecture

The primary database tables are:

```text
products
inventory
suppliers
restock_orders
yard_docks
deliveries
tracking_events
alerts
shipment_integrations
```

Simplified relationship model:

```text
Product ───────── Inventory
   │
   ▼
RestockOrder ◄──── Supplier
   │
   ▼
Delivery ───────── YardDock
   │
   ├──────────────► TrackingEvent
   │
   └──────────────► Alert

External System
      │
      ▼
ShipmentIntegration
      │
      ▼
RestockOrder / Delivery
```

## Shipment Integration Table

The `shipment_integrations` table stores information received from external systems.

Its purpose is to maintain separation between external procurement systems and E2's internal logistics database.

This allows PR2 and E2 to maintain separate databases while communicating through REST APIs.

---

# 10. API Architecture

Main API groups include:

```text
/
├── /health
├── /api/status
├── /products
├── /inventory
├── /suppliers
├── /restock-orders
├── /yard-docks
├── /deliveries
├── /integrations
├── /tracking
├── /eta
├── /simulation
├── /dock-operations
├── /dock-recommendation
├── /operations
└── /dashboard
```

---

# 11. System APIs

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Backend information |
| GET | `/health` | Application/database health |
| GET | `/api/status` | Backend capability/status information |

---

# 12. Products

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/products/` | Create product |
| GET | `/products/` | List products |
| GET | `/products/{product_id}` | Get product |
| DELETE | `/products/{product_id}` | Delete product |

Example:

```json
{
  "sku": "SKU-1001",
  "name": "Industrial Bearing",
  "category": "Mechanical",
  "unit_price": 450.50,
  "reorder_level": 25
}
```

---

# 13. Inventory

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/inventory/` | List inventory |
| GET | `/inventory/{product_id}` | Get inventory |
| POST | `/inventory/` | Create inventory |
| PUT | `/inventory/{product_id}` | Update inventory |

---

# 14. Suppliers

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/suppliers/` | List suppliers |
| GET | `/suppliers/{supplier_id}` | Get supplier |
| POST | `/suppliers/` | Create supplier |
| PUT | `/suppliers/{supplier_id}` | Update supplier |
| DELETE | `/suppliers/{supplier_id}` | Delete supplier |

---

# 15. Restock Orders

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/restock-orders/` | Create order |
| GET | `/restock-orders/` | List orders |
| GET | `/restock-orders/{order_id}` | Get order |
| PUT | `/restock-orders/{order_id}/status` | Update status |
| DELETE | `/restock-orders/{order_id}` | Delete order |

Example:

```json
{
  "product_id": 1,
  "supplier_id": 1,
  "quantity": 100,
  "status": "pending",
  "expected_delivery": "2026-08-28T10:00:00"
}
```

---

# 16. Yard Docks

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/yard-docks/` | Create dock |
| GET | `/yard-docks/` | List docks |
| GET | `/yard-docks/{dock_id}` | Get dock |
| PUT | `/yard-docks/{dock_id}` | Update dock |
| DELETE | `/yard-docks/{dock_id}` | Delete dock |

Dock states can include:

```text
available
occupied
reserved
maintenance
blocked
```

Dock compatibility includes:

```text
Dock Type
Supported Vehicle Type
Maximum Vehicle Length
Refrigerated Support
Hazardous Load Support
```

---

# 17. Deliveries

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/deliveries/` | Create shipment |
| GET | `/deliveries/` | List shipments |
| GET | `/deliveries/{delivery_id}` | Get shipment |
| GET | `/deliveries/tracking/{tracking_number}` | Lookup shipment |
| PUT | `/deliveries/{delivery_id}/status` | Update shipment status |

Delivery contains operational information such as:

```text
Tracking Number
Trailer ID
Shipment Reference
Carrier
Status
Scheduled Arrival
Actual Arrival
Current GPS
Destination GPS
Estimated Arrival
ETA
Distance Remaining
Delay Flag
Exception Flag
Dock Assignment
```

---

# 18. External Shipment Integration

E2 exposes a dedicated endpoint for receiving shipments from another backend.

```http
POST /integrations/shipments
```

This is the primary **PR2 → E2 integration endpoint**.

Production endpoint:

```text
https://e2-backend.onrender.com/integrations/shipments
```

Example request:

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

Successful creation returns:

```http
201 Created
```

The imported shipment becomes a normal E2 delivery and can use the rest of the E2 functionality.

```text
PR2
 ↓
Integration Endpoint
 ↓
E2 Delivery
 ↓
Tracking
 ↓
ETA
 ↓
Delay Monitoring
 ↓
Yard
 ↓
Dock Scheduling
 ↓
Dashboard
```

---

# 19. Shipment Tracking

E2 supports multiple shipment identifiers.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/tracking/shipment/{tracking_number}` | Lookup by tracking number |
| GET | `/tracking/shipment/id/{delivery_id}` | Lookup by delivery ID |
| GET | `/tracking/trailer/{trailer_id}` | Lookup by trailer ID |
| GET | `/tracking/reference/{shipment_reference}` | Lookup by shipment reference |
| POST | `/tracking/{delivery_id}/events` | Add tracking event |
| GET | `/tracking/{delivery_id}/events` | Tracking history |
| GET | `/tracking/active` | Active shipments |

Example tracking event:

```json
{
  "status": "in_transit",
  "location": "Kolkata",
  "latitude": 22.5726,
  "longitude": 88.3639,
  "event_time": "2026-08-25T12:00:00",
  "description": "Truck departed distribution centre"
}
```

---

# 20. ETA Prediction

E2 supports dynamic ETA calculation and machine-learning delivery prediction.

## Basic ETA

```http
GET /eta/predict
```

## ML Delivery Prediction

```http
POST /eta/predict-delivery/{delivery_id}
```

Example:

```http
POST /eta/predict-delivery/2?supplier_delay_history=0&carrier_delay_history=0&delay_threshold_minutes=15
```

The ML prediction uses:

```text
Distance Remaining
Quantity
Supplier Delay History
Carrier Delay History
```

The model is:

```text
RandomForestRegressor
```

Model location:

```text
app/ml/saved_models/eta_model.pkl
```

Prediction flow:

```text
Delivery
   ↓
Distance Remaining
   +
Quantity
   +
Supplier History
   +
Carrier History
   ↓
Feature Preparation
   ↓
Random Forest Regressor
   ↓
Estimated Delivery Hours
   ↓
Estimated Arrival
   ↓
Compare Scheduled Arrival
   ↓
Predicted Delay
   ↓
Delay Flag / Alert
```

---

# 21. GPS Simulation

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/simulation/start/{delivery_id}` | Start simulation |
| POST | `/simulation/step/{delivery_id}` | Advance simulation |
| POST | `/simulation/stop/{delivery_id}` | Stop simulation |

Simulation updates:

```text
Latitude
Longitude
Current Location
Speed
Distance Remaining
ETA
Estimated Arrival
Shipment Status
```

This provides logistics demonstrations without requiring external GPS hardware.

---

# 22. Dock Recommendation

```http
POST /dock-recommendation/
```

The recommendation engine evaluates dock candidates based on operational conditions.

Example:

```json
{
  "docks": [
    {
      "id": 1,
      "dock_number": "D-01",
      "yard_name": "Main Yard",
      "status": "available",
      "dock_type": "general",
      "available_in_hours": 0
    }
  ],
  "truck_eta_hours": 2,
  "priority": "normal",
  "load_type": "general"
}
```

---

# 23. Dock Operations

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/dock-operations/recommend/{delivery_id}` | Recommend docks |
| GET | `/dock-operations/schedule` | Retrieve dock schedule |
| POST | `/dock-operations/assign/{delivery_id}` | Assign dock |
| POST | `/dock-operations/reassign/{delivery_id}` | Reassign dock |
| POST | `/dock-operations/auto-reassign/{delivery_id}` | Automatically reassign dock |

The recommendation layer provides decision support while assignment endpoints modify operational state.

---

# 24. Delay Detection

```http
POST /operations/detect-delays
```

Conceptually:

```text
Scheduled Arrival
        +
Estimated Arrival
        ↓
Delay Evaluation
        ↓
Delay Detected?
     ┌──────┴──────┐
     No            Yes
                    ↓
              Update Delivery
                    ↓
                Create Alert
```

---

# 25. Exception Detection

```http
POST /operations/detect-exceptions
```

Exception monitoring identifies abnormal shipment conditions.

Examples include missing GPS information while shipment tracking or simulation is expected to be active.

E2 distinguishes between:

```text
Business / Schedule Delay
```

and:

```text
Operational / Tracking Exception
```

---

# 26. Alerts

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/operations/alerts` | Get unresolved alerts |
| PUT | `/operations/alerts/{alert_id}/resolve` | Resolve alert |

Example:

```json
{
  "severity": "critical",
  "message": "GPS location has not been received",
  "delivery_id": 2,
  "alert_type": "exception",
  "title": "Shipment Exception",
  "resolved": false
}
```

---

# 27. Dashboard

Core endpoints include:

```text
GET /dashboard/summary
GET /dashboard/live-shipments
GET /dashboard/dock-status
GET /dashboard/yard-status
GET /dashboard/dock-schedule
GET /dashboard/trailer-door-allocation
GET /dashboard/insights
```

Dashboard information includes:

```text
Shipments
Docks
Inventory
Alerts
Yard State
Dock Schedule
Trailer Allocation
Operational Insights
```

---

# 28. Yard Status

```http
GET /dashboard/yard-status
```

Provides an operational view of active trailers.

Summary fields include:

```text
total_active_trailers
at_gate
in_yard
waiting_for_dock
dock_assigned
docked_or_unloading
delayed
```

Trailer information can include:

```text
Delivery ID
Tracking Number
Trailer ID
Shipment Reference
Carrier
Status
Operational State
Yard Location
GPS
Scheduled Arrival
Estimated Arrival
Actual Arrival
ETA
Distance Remaining
Delay Flag
Exception Flag
Assigned Dock
```

---

# 29. Dock Scheduling

```http
GET /dashboard/dock-schedule
```

The scheduler creates operational time windows for incoming trailers.

Current slot duration:

```text
30 minutes
```

Scheduling considers:

```text
Existing Dock Assignment
Dock Compatibility
Dock Availability
Existing Scheduled Slots
Arrival Time
Waiting Time
Operational Priority
```

Flow:

```text
Incoming Trailer
       ↓
Determine Effective Arrival
       ↓
Evaluate Compatible Docks
       ↓
Check Existing Slots
       ↓
Calculate Earliest Available Window
       ↓
Score Candidate Dock
       ↓
Select Best Dock
       ↓
Create 30-Minute Window
```

---

# 30. Trailer-Door Allocation

```http
GET /dashboard/trailer-door-allocation
```

This endpoint combines current assignments with dock-scheduling recommendations.

It determines whether each trailer:

```text
Has a valid current assignment
Needs an assignment
Needs reassignment
Cannot currently be scheduled
```

Possible states include:

```text
CURRENT_ASSIGNMENT_VALID
REASSIGNMENT_RECOMMENDED
```

---

# 31. Background Processing

E2 contains an asynchronous background tracking loop.

```text
Find Active Simulations
        ↓
Read Current GPS
        ↓
Move Toward Destination
        ↓
Update GPS
        ↓
Calculate Remaining Distance
        ↓
Calculate ETA
        ↓
Update Estimated Arrival
        ↓
Check Arrival Condition
        ↓
Persist State
        ↓
Repeat
```

This allows shipment state to evolve while the backend is running without requiring continuous frontend actions.

---

# 32. Installation & Setup

## Prerequisites

Install:

```text
Python
PostgreSQL
pip
Git
```

Clone the repository:

```bash
git clone https://github.com/PriyankaA1807/E2-backend.git
cd E2-backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Windows:

```powershell
venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 33. Environment Configuration

Create a `.env` file in the project root for local development.

```env
DATABASE_URL=postgresql://USERNAME:PASSWORD@HOST:PORT/DATABASE_NAME
```

For production, `DATABASE_URL` is configured through Render environment variables.

**Never commit real database credentials.**

The repository `.gitignore` should contain:

```text
.env
.env.*
!.env.example
```

The public repository should contain only placeholder values in `.env.example`.

Example:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/e2_database
```

---

# 34. Running the Application

## Local Development

```bash
uvicorn app.main:app --reload
```

Local backend:

```text
http://127.0.0.1:8000
```

Local Swagger:

```text
http://127.0.0.1:8000/docs
```

## Production

Production backend:

```text
https://e2-backend.onrender.com
```

---

# 35. Swagger / OpenAPI

FastAPI automatically exposes interactive API documentation.

## Production Swagger UI

```text
https://e2-backend.onrender.com/docs
```

## Production OpenAPI Schema

```text
https://e2-backend.onrender.com/openapi.json
```

## Local Swagger UI

```text
http://127.0.0.1:8000/docs
```

## Local OpenAPI Schema

```text
http://127.0.0.1:8000/openapi.json
```

Frontend and integration developers should use Swagger/OpenAPI as the authoritative API contract for the running backend.

---

# 36. Testing

The backend can be tested through Swagger.

Recommended end-to-end sequence:

```text
1. Create Product
2. Create Inventory
3. Create Supplier
4. Create Restock Order
5. Create Yard Dock
6. Create Delivery
7. Add Tracking Event
8. Retrieve Tracking History
9. Start GPS Simulation
10. Observe GPS / ETA
11. Run ML ETA Prediction
12. Detect Delay
13. Detect Exceptions
14. Retrieve Alerts
15. Resolve Alert
16. Request Dock Recommendation
17. Assign Dock
18. Retrieve Yard Status
19. Retrieve Dock Schedule
20. Retrieve Trailer-Door Allocation
21. Retrieve Dashboard Summary
22. Send PR2 Integration Shipment
23. Verify Imported Delivery
24. Lookup Imported Shipment by Tracking Number
25. Lookup Imported Shipment by Trailer ID
26. Lookup Imported Shipment by Shipment Reference
```

The production Swagger interface can be used for deployment testing:

```text
https://e2-backend.onrender.com/docs
```

A dedicated automated test suite using `pytest` can be added in a future version.

---

# 37. Frontend Integration

The FastAPI backend should be treated as the source of truth for E2 logistics state.

Production base URL:

```text
https://e2-backend.onrender.com
```

Frontend API mapping:

```text
Frontend
   │
   ├── Products ───────────────► /products
   ├── Inventory ──────────────► /inventory
   ├── Suppliers ──────────────► /suppliers
   ├── Procurement ────────────► /restock-orders
   ├── Deliveries ─────────────► /deliveries
   ├── Tracking Map ───────────► /tracking
   ├── ETA ────────────────────► /eta
   ├── Yard UI ────────────────► /dashboard/yard-status
   ├── Dock Schedule ──────────► /dashboard/dock-schedule
   ├── Trailer Allocation ─────► /dashboard/trailer-door-allocation
   ├── Dock Assignment ────────► /dock-operations
   ├── Alerts ─────────────────► /operations
   └── Dashboard ──────────────► /dashboard
```

For example:

```text
https://e2-backend.onrender.com/dashboard/summary
```

Frontend developers should use the production Swagger/OpenAPI documentation to verify request and response schemas.

---

# 38. PR2 Integration

PR2 and E2 maintain **separate databases**.

They communicate using REST APIs rather than sharing database tables directly.

```text
┌────────────────────────┐
│      PR2 Backend       │
│ Procurement / Orders   │
└────────────┬───────────┘
             │
             │ HTTP POST / JSON
             ▼
┌───────────────────────────────┐
│         E2 Backend            │
│ POST /integrations/shipments  │
└────────────┬──────────────────┘
             │
             ▼
┌────────────────────────┐
│ shipment_integrations  │
└────────────┬───────────┘
             │
             ├──────────► Restock Order
             │
             └──────────► Delivery
                              │
                              ▼
                         E2 Workflow
```

## Production Integration Endpoint

```text
https://e2-backend.onrender.com/integrations/shipments
```

PR2 sends:

```http
POST /integrations/shipments
```

with a JSON body following the E2 integration contract.

Example:

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

E2 then handles the logistics workflow.

PR2 does **not** need direct access to the E2 PostgreSQL database.

---

# 39. Design Decisions

## Why FastAPI?

FastAPI provides:

- type-based request validation;
- Pydantic integration;
- automatic OpenAPI generation;
- Swagger UI;
- async support;
- high API performance;
- straightforward Python ML integration.

## Why PostgreSQL?

E2 contains strongly related business entities:

```text
Products
Suppliers
Inventory
Orders
Deliveries
Docks
Tracking Events
Alerts
Integration Records
```

A relational database provides appropriate integrity and transactional support.

## Why SQLAlchemy?

SQLAlchemy provides:

- ORM-based persistence;
- relationships;
- query abstraction;
- cleaner business logic;
- database portability;
- maintainable model definitions.

## Why Separate PR2 and E2 Databases?

Directly sharing one database would tightly couple two independently developed systems.

```text
PR2 Database
     ↓
REST API
     ↓
E2 Database
```

This provides clearer ownership and lower coupling.

## Why Random Forest for ETA?

Shipment travel time can depend on interacting structured features.

Random Forest:

- handles nonlinear relationships;
- models feature interactions;
- works well with tabular data;
- requires less complexity than a neural network;
- is straightforward to train and deploy.

## Why Separate Routers?

Business functionality is separated into domain modules.

```text
deliveries.py
tracking.py
eta.py
operations.py
dashboard.py
integrations.py
```

This improves maintainability, readability, debugging, testing, team ownership, and API integration.

## Why Background Tracking?

Shipment state changes with time.

A background process allows simulated shipment movement and ETA updates even when the frontend is not actively making requests.

## Why Dock Scheduling?

Dock recommendation alone identifies a suitable dock but does not address time conflicts.

```text
Dock Compatibility
+
Arrival Time
+
Existing Reservations
+
Operational Priority
=
Dock + Time Window
```

## Why Trailer-Door Allocation?

A previously assigned dock may become blocked, occupied, or otherwise unsuitable.

Trailer-door allocation compares current assignments with the latest schedule and identifies when reassignment is required.

---

# 40. Current Limitations

The current project scope does not yet include all production-level infrastructure.

Current limitations include:

- no full authentication/authorization layer;
- no production-grade API gateway;
- no distributed message queue;
- no real GPS/telematics provider;
- simulation is used for GPS demonstrations;
- no automated pytest suite yet;
- no Alembic migration workflow yet;
- ML model is based on project/training data rather than large-scale production logistics history;
- external integration currently uses REST rather than an event-driven message broker.

These limitations do not prevent the current frontend/backend integration or project demonstration.

---

# 41. Future Improvements

## Security

- JWT authentication
- Role-based authorization
- API keys for service-to-service integration
- Rate limiting
- Audit logging

## Database

- Alembic migrations
- Additional indexes
- Transaction hardening
- Database monitoring
- Automated backups for production environments

## Integration

- Integration authentication
- Idempotency keys
- Retry policies
- Webhooks
- Kafka/RabbitMQ event integration
- Dead-letter queues

## Testing

- Pytest
- Unit tests
- Integration tests
- API contract tests
- CI testing

## Infrastructure

Currently implemented:

- Cloud deployment using Render
- Managed PostgreSQL database
- GitHub-connected deployment
- Production environment variables

Future improvements:

- Docker
- Docker Compose
- CI/CD testing pipeline
- Production scaling configuration
- Multiple deployment environments

## Real-Time Logistics

- WebSockets
- Live frontend shipment updates
- Real GPS/IoT integration
- Message queues
- Event-driven processing

## Machine Learning

- Larger historical ETA dataset
- Model evaluation metrics
- Model versioning
- Feature monitoring
- Retraining pipeline
- Prediction confidence monitoring

## Observability

- Structured logging
- Metrics
- Health monitoring
- Distributed tracing
- Error monitoring

---

# 42. Deployment

E2 is deployed on **Render** as a Python Web Service.

## Production Backend

```text
https://e2-backend.onrender.com
```

## Production Swagger UI

```text
https://e2-backend.onrender.com/docs
```

## Production OpenAPI Schema

```text
https://e2-backend.onrender.com/openapi.json
```

## Production Database

The production backend uses a managed PostgreSQL database hosted on Render.

The database connection is supplied to the application using:

```env
DATABASE_URL=<Render PostgreSQL connection URL>
```

The actual database username, password, hostname, and other credentials are stored securely in Render and are **not committed to GitHub**.

## Render Build Command

```bash
pip install -r requirements.txt
```

## Render Start Command

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Deployment Architecture

```text
GitHub
   │
   │ Source Code
   ▼
Render Web Service
   │
   │ Build
   ▼
Install requirements.txt
   │
   ▼
Start Uvicorn
   │
   ▼
FastAPI Application
   │
   ├────────► Render PostgreSQL
   │
   ├────────► ML ETA Model
   │
   └────────► Background Tracking
   │
   ▼
Public REST API
   │
   ├────────► Frontend
   └────────► PR2 / External Systems
```

## Deployment Status

```text
Web Service: Live
Database: Available
Runtime: Python 3
Database Engine: PostgreSQL
```

The Render free Web Service may spin down after a period of inactivity. Therefore, the first request after an idle period can take longer than normal.

---

# 43. Project Status

**E2 backend implementation is operational, cloud-deployed, and ready for frontend and cross-service integration at the current project scope.**

Production backend:

```text
https://e2-backend.onrender.com
```

Production Swagger:

```text
https://e2-backend.onrender.com/docs
```

Implemented capabilities include:

- Product management
- Inventory management
- Supplier management
- Restock-order management
- Delivery management
- External PR2 shipment integration
- Shipment integration persistence
- Tracking-number lookup
- Delivery-ID lookup
- Trailer-ID lookup
- Shipment-reference lookup
- Tracking-event history
- GPS simulation
- Dynamic ETA calculation
- Random Forest ETA prediction
- Predicted delay evaluation
- Delay detection
- Exception detection
- Operational alerts
- Alert resolution
- Yard/dock management
- Dock recommendation
- Dock assignment
- Dock reassignment
- Automatic dock reassignment
- Yard-status dashboard
- Dock scheduling
- Trailer-door allocation
- Operational insights
- Background shipment tracking
- Swagger/OpenAPI documentation
- Render cloud deployment
- Managed PostgreSQL database

The PR2 → E2 integration flow uses:

```http
POST /integrations/shipments
```

Production:

```text
https://e2-backend.onrender.com/integrations/shipments
```

Imported shipments can subsequently be retrieved through:

```text
GET /deliveries/
GET /tracking/shipment/{tracking_number}
GET /tracking/trailer/{trailer_id}
GET /tracking/reference/{shipment_reference}
```

---

# 44. Repository

GitHub Repository:

```text
PriyankaA1807/E2-backend
```

---

# API Documentation

Detailed API documentation is maintained separately in the `api-docs/` directory.

```text
api-docs/
├── README.md
├── products-api.md
├── inventory-api.md
├── suppliers-api.md
├── restock-orders-api.md
├── deliveries-api.md
├── integrations-api.md
├── tracking-api.md
├── eta-api.md
├── simulation-api.md
├── yard-docks-api.md
├── dock-operations-api.md
├── operations-api.md
└── dashboard-api.md
```

Production API base URL:

```text
https://e2-backend.onrender.com
```

Production Swagger:

```text
https://e2-backend.onrender.com/docs
```

---

# E2 — Smart Restock & Yard Dock Delivery Tracker

**FastAPI + PostgreSQL + SQLAlchemy + Machine Learning + GPS Simulation + Shipment Integration + Yard Operations + Intelligent Dock Scheduling + Render Deployment**
