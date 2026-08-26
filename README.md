# E2 Smart Restock & Yard Dock Delivery Tracker

Backend API for the **E2 Smart Restock & Yard Dock Delivery Tracker**.

The project focuses on inbound delivery tracking, simulated real-time truck movement, ETA prediction, delay detection, yard visibility, dock recommendation, dock assignment, and operational alerts.

The backend is built using **FastAPI, PostgreSQL, SQLAlchemy, and Python**, with a **Random Forest Regression model** for ETA prediction.

---

## Project Objective

The goal of this project is to provide visibility into inbound trucks and trailers approaching a warehouse or yard.

The system can:

- Track inbound deliveries
- Track shipments using tracking number, delivery ID, trailer ID, or shipment reference
- Simulate real-time truck GPS movement
- Automatically update truck locations in the background
- Calculate remaining distance
- Predict ETA using a machine learning model
- Detect shipment delays
- Generate operational alerts
- Show yard and dock availability
- Recommend compatible docks
- Assign and reassign docks
- Detect arrival at the yard gate
- Provide a simulated WMS feed
- Provide operational dashboard data

---

## Main Features

### 1. Delivery Management

The backend manages inbound deliveries connected to restock orders.

Each delivery can contain information such as:

- Tracking number
- Trailer ID
- Shipment reference
- Carrier
- Scheduled arrival
- Estimated arrival
- Actual arrival
- Current location
- Destination location
- Delivery status
- Assigned dock

---

### 2. Shipment Tracking

Shipments can be searched using:

- Tracking number
- Delivery ID
- Trailer ID
- Shipment reference

Tracking information includes:

- Current latitude
- Current longitude
- Current location
- Destination coordinates
- Remaining distance
- ETA
- Shipment status
- Delay status
- Simulation status
- Last GPS update

---

### 3. Simulated Real-Time GPS Tracking

The project uses **simulated real-time GPS tracking** for the hackathon.

A simulation is started once for a delivery:

```http
POST /simulation/start/{delivery_id}
```

After the simulation starts, the backend automatically updates the truck's GPS coordinates in the background.

The frontend does not need to repeatedly call the simulation step endpoint.

The flow is:

```text
Start Simulation
        ↓
simulation_active = true
        ↓
Background tracking loop
        ↓
Truck coordinates change automatically
        ↓
Remaining distance recalculated
        ↓
ETA recalculated
        ↓
Frontend reads latest tracking data
        ↓
Truck marker moves on map
```

The frontend can periodically call a tracking endpoint such as:

```http
GET /tracking/shipment/id/{delivery_id}
```

and use the latest:

```text
current_latitude
current_longitude
distance_remaining_km
eta_minutes
status
```

to update the truck marker on the map.

This provides a simulated real-time tracking experience without requiring a physical GPS device.

---

## Automatic Background Tracking

The backend contains a background tracking process for deliveries where:

```text
simulation_active = true
```

While a simulation is active, the backend automatically:

1. Moves the truck toward its destination
2. Updates latitude and longitude
3. Calculates remaining distance
4. Recalculates ETA
5. Checks for delays
6. Stores tracking events
7. Detects arrival at the yard gate

The background process runs automatically after the simulation has been started.

The `/simulation/step/{delivery_id}` endpoint is retained mainly for manual API testing and demonstration purposes.

---

## ETA Prediction

The project uses a trained:

```text
RandomForestRegressor
```

for ETA prediction.

The trained model is stored at:

```text
app/ml/saved_models/eta_model.pkl
```

### Model Features

The ETA model uses:

```text
distance_km
quantity
supplier_delay_history
carrier_delay_history
```

### Hackathon Data Usage

For the hackathon prototype:

**distance_km**

Calculated dynamically from the simulated truck's current GPS position and the destination.

**quantity**

Obtained from the linked restock order.

**supplier_delay_history**

Uses a prototype/default value during automatic simulation.

**carrier_delay_history**

Uses a prototype/default value during automatic simulation.

In a production system, supplier and carrier delay history could come from historical WMS/TMS or logistics performance data.

---

## Dynamic ETA During Truck Movement

ETA is not fixed after the simulation starts.

As the simulated truck moves:

```text
New GPS Position
       ↓
Remaining Distance
       ↓
Random Forest ETA Model
       ↓
Updated ETA
       ↓
Updated Estimated Arrival
```

Therefore, the ETA can change throughout the simulated journey.

---

## Delay Detection

The backend compares the predicted arrival time with the scheduled arrival time.

If the predicted arrival exceeds the configured delay threshold, the delivery can be marked as delayed.

Example:

```text
Scheduled Arrival
        ↓
Predicted Arrival
        ↓
Compare
        ↓
Predicted arrival too late?
        ↓
YES
        ↓
delay_detected = true
        ↓
Delay Alert
```

Duplicate unresolved delay alerts are avoided.

---

## Operational Alerts

The system supports operational alerts such as:

- Predicted shipment delay
- Missing GPS information
- Shipment exception
- Dock unavailable
- Dock reassignment required

For this hackathon project, the application uses a **single Operations Admin view**.

There is no complex authentication or role-management system required for the prototype.

All unresolved operational alerts can be displayed on the Operations Admin dashboard.

Example endpoint:

```http
GET /operations/alerts
```

---

## Arrival Detection

The system automatically detects when the simulated truck reaches the yard.

When the truck reaches the arrival threshold, the backend:

```text
Moves truck exactly to destination coordinates
        ↓
status = arrived_at_gate
        ↓
current_location = Yard Gate
        ↓
distance_remaining_km = 0
        ↓
eta_minutes = 0
        ↓
actual_arrival = current time
        ↓
simulation_active = false
```

Therefore, the simulation automatically stops after arrival.

---

## Delivery Lifecycle

A typical delivery lifecycle can be represented as:

```text
scheduled
    ↓
in_transit
    ↓
delayed (if required)
    ↓
arrived_at_gate
    ↓
in_yard
    ↓
waiting_for_dock
    ↓
dock_assigned
    ↓
docked
    ↓
unloading
    ↓
completed
```

Not every delivery must enter the `delayed` state.

---

## Yard and Dock Management

The system provides visibility into warehouse yard docks.

Dock information can include:

- Yard name
- Dock number
- Dock status
- Dock type
- Supported vehicle type
- Maximum vehicle length
- Refrigeration capability
- Hazardous-material capability

The backend supports:

- Dock availability
- Dock compatibility checking
- Dock recommendation
- Dock assignment
- Dock reassignment
- Automatic reassignment support

---

## Dock Recommendation

The dock recommendation module helps select an appropriate dock for an arriving delivery.

Recommendations can consider dock compatibility and availability.

This helps operations determine where an inbound trailer should be assigned after reaching the yard.

---

## Simulated WMS Feed

The project includes a simulated Warehouse Management System feed.

Example:

```http
GET /simulation/wms-feed
```

The feed combines current trailer and dock information.

It can provide:

- Total trailers
- Active shipments
- Delayed shipments
- Trucks waiting for docks
- Total docks
- Available docks
- Trailer locations
- ETA information
- Delay information
- Assigned docks

This allows the frontend to consume a WMS-style operational feed without requiring access to a real enterprise WMS.

---

## Operations Dashboard

The backend provides data that can be used by a frontend Operations Admin dashboard.

The dashboard can display:

```text
Active Deliveries
Delayed Deliveries
Incoming Trucks
Current ETA
Truck Location
Yard Status
Available Docks
Assigned Docks
Operational Alerts
```

Only one Operations Admin view is required for the hackathon prototype.

---

## Frontend Map Integration

The frontend can display the simulated truck on a map using:

```text
current_latitude
current_longitude
destination_latitude
destination_longitude
```

The recommended frontend flow is:

```text
POST /simulation/start/{delivery_id}
              ↓
Start simulation once
              ↓
GET tracking information every few seconds
              ↓
Receive new latitude/longitude
              ↓
Update truck marker
              ↓
Receive updated ETA and distance
              ↓
Update UI
```

The frontend should **not** need to continuously call:

```http
POST /simulation/step/{delivery_id}
```

because automatic movement is handled by the backend background tracking process.

---

## Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- Uvicorn

### Database

- PostgreSQL

### Machine Learning

- Scikit-learn
- Random Forest Regressor
- Pandas
- Joblib

### API Documentation

- Swagger UI
- OpenAPI

### Deployment

- Render
- AWS deployment can also be used

---

## Project Structure

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
│   │   ├── operations.py
│   │   ├── dock_operations.py
│   │   ├── dock_recommendation.py
│   │   └── dashboard.py
│   │
│   └── ml/
│       ├── eta.py
│       ├── eta_predictor.py
│       ├── train_eta_model.py
│       ├── dock_recommender.py
│       │
│       └── saved_models/
│           └── eta_model.pkl
│
├── api-docs/
│
├── requirements.txt
└── README.md
```

---

## Running the Project Locally

### 1. Clone the repository

```bash
git clone <repository-url>
```

Move into the project:

```bash
cd E2-backend
```

---

### 2. Create a virtual environment

Windows:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure Environment Variables

Create a `.env` file and configure the PostgreSQL database connection required by the project.

Do not commit database passwords or other secrets to GitHub.

---

### 5. Start the backend

```bash
uvicorn app.main:app --reload
```

The local API will run at:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

When the application starts successfully, the terminal should show that the application startup completed and the E2 background tracking process started.

---

## Example Hackathon Demo Flow

A simple end-to-end demonstration can follow this sequence:

### Step 1 — Check Yard Docks

```http
GET /yard-docks
```

Show available warehouse docks.

### Step 2 — Check Restock Orders

```http
GET /restock-orders
```

Select the order associated with the inbound goods.

### Step 3 — Create Delivery

```http
POST /deliveries
```

Save:

```text
delivery_id
tracking_number
```

### Step 4 — Find Delivery

```http
GET /deliveries
```

Confirm that the delivery exists.

### Step 5 — Track by Tracking Number

```http
GET /tracking/shipment/{tracking_number}
```

This can represent shipment tracking using the tracking number.

### Step 6 — Track Internally by Delivery ID

```http
GET /tracking/shipment/id/{delivery_id}
```

Operations can use the delivery ID to retrieve the same shipment.

### Step 7 — Start Simulated Real-Time Tracking

```http
POST /simulation/start/{delivery_id}
```

Call this only once.

The backend then automatically moves the truck.

### Step 8 — Read Updated Tracking Data

```http
GET /tracking/shipment/id/{delivery_id}
```

Call periodically.

The frontend will observe:

```text
latitude changing
longitude changing
distance decreasing
ETA changing
status changing
```

### Step 9 — Detect Delay

If predicted arrival is later than scheduled arrival, the system automatically detects the delay.

Operational alerts can be viewed using:

```http
GET /operations/alerts
```

### Step 10 — Truck Reaches Yard

The backend automatically changes the delivery to:

```text
arrived_at_gate
```

and sets:

```text
distance_remaining_km = 0
eta_minutes = 0
simulation_active = false
```

### Step 11 — Recommend / Assign Dock

Use the dock operations endpoints to recommend and assign an appropriate dock.

### Step 12 — Complete Yard Process

The delivery can continue through the yard/dock lifecycle until completion.

---

## Simulated Real-Time vs Real GPS

This project should be described as:

> **Simulated real-time truck tracking**

The backend automatically produces changing GPS coordinates over time.

It is **not connected to a physical truck GPS device**.

For a production implementation, the simulation layer could be replaced with data from:

- GPS/telematics providers
- Fleet-management systems
- Carrier APIs
- IoT tracking devices
- Enterprise transportation-management systems

The remaining ETA, alert, tracking, and dock-management architecture could continue to process those incoming locations.

---

## Hackathon Scope

This project intentionally focuses on demonstrating the core E2 workflow rather than implementing a complete enterprise identity system.

The hackathon version uses:

- One Operations Admin view
- No complex signup/login flow
- No multi-role authentication system
- Simulated WMS data
- Simulated real-time GPS movement
- ML-based ETA prediction
- Automatic delay detection
- Operational alerts
- Yard and dock management

This keeps the prototype focused on the core logistics problem.

---

## API Documentation

Detailed endpoint documentation is available inside:

```text
api-docs/
```

The documentation is separated by module so frontend and other team members can integrate individual backend components easily.

---

## Current Project Status

Implemented:

- Delivery management
- Shipment tracking
- Tracking by multiple identifiers
- Simulated GPS tracking
- Automatic background truck movement
- Remaining-distance calculation
- Random Forest ETA prediction
- Dynamic ETA updates during simulation
- Delay detection
- Exception detection
- Operational alerts
- Yard management
- Dock compatibility
- Dock recommendation
- Dock assignment
- Dock reassignment
- Simulated WMS feed
- Operations dashboard support
- Automatic yard-gate arrival detection
- Automatic simulation stop after arrival

The backend is ready for frontend integration of the simulated real-time map experience.
