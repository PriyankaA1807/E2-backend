# E2 Backend API Documentation

API documentation for the E2 Smart Restock & Yard Dock Delivery Tracker.

## Base URL

`http://127.0.0.1:8000`

## API Modules

| Module | Documentation |
|---|---|
| Products | [products-api.md](products-api.md) |
| Inventory | [inventory-api.md](inventory-api.md) |
| Suppliers | [suppliers-api.md](suppliers-api.md) |
| Restock Orders | [restock-orders-api.md](restock-orders-api.md) |
| Deliveries | [deliveries-api.md](deliveries-api.md) |
| Tracking | [tracking-api.md](tracking-api.md) |
| ETA Prediction | [eta-api.md](eta-api.md) |
| GPS Simulation | [simulation-api.md](simulation-api.md) |
| Yard Docks | [yard-docks-api.md](yard-docks-api.md) |
| Dock Operations | [dock-operations-api.md](dock-operations-api.md) |
| Operations & Alerts | [operations-api.md](operations-api.md) |
| Dashboard | [dashboard-api.md](dashboard-api.md) |

## End-to-End Flow

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
Tracking / GPS Simulation
   ↓
ETA & Operational Monitoring
   ↓
Alerts
   ↓
Dock Recommendation
   ↓
Dock Assignment
   ↓
Dashboard

## API Conventions

- No `/api/v1` prefix is currently used.
- No authentication is currently implemented.
- Errors use FastAPI's standard `detail` response.
- List APIs currently do not use pagination.
- Live shipment updates currently use HTTP polling rather than WebSockets.

For request bodies, response structures, validation rules, errors,
backend behavior and frontend integration, see the individual API
documentation files above.
