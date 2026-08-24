# E2 Backend

Smart Restock & Yard Dock Delivery Tracker backend built with FastAPI.

## Features

* Delivery and shipment tracking
* GPS simulation
* ETA prediction
* Yard and dock management
* Dock recommendation and assignment
* Delay and exception detection
* Alerts and alert resolution
* Dashboard and operational insights
* Automatic background tracking

## Tech Stack

* Python
* FastAPI
* SQLAlchemy
* PostgreSQL
* Pandas
* Scikit-learn
* Random Forest
* Uvicorn

## Setup

Create and activate a virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
```

Create your `.env` file with the required database configuration.

Run the backend:

```bash
uvicorn app.main:app --reload
```

Server:

```text
http://127.0.0.1:8000
```

Swagger documentation:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
GET /health
```

API status:

```text
GET /api/status
```

## ETA Model

The trained ETA model is stored at:

```text
app/ml/saved_models/eta_model.pkl
```

## Status

Backend completed and ready for frontend integration.
