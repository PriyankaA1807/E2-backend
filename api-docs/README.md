# E2 Backend API Documentation

API documentation for the **E2 Smart Restock & Yard Dock Delivery Tracker**.

## Base URL

```text
https://e2-backend.onrender.com
```

Swagger:

```text
https://e2-backend.onrender.com/docs
```

---

## API Modules

| Module | Documentation |
|---|---|
| Products | [products-api.md](products-api.md) |
| Inventory | [inventory-api.md](inventory-api.md) |
| Suppliers | [suppliers-api.md](suppliers-api.md) |
| Restock Orders | [restock-orders-api.md](restock-orders-api.md) |
| Deliveries | [deliveries-api.md](deliveries-api.md) |
| Integrations | [integrations-api.md](integrations-api.md) |
| Tracking | [tracking-api.md](tracking-api.md) |
| ETA Prediction | [eta-api.md](eta-api.md) |
| GPS Simulation | [simulation-api.md](simulation-api.md) |
| Yard Docks | [yard-docks-api.md](yard-docks-api.md) |
| Dock Operations | [dock-operations-api.md](dock-operations-api.md) |
| Operations & Alerts | [operations-api.md](operations-api.md) |
| Dashboard | [dashboard-api.md](dashboard-api.md) |

---

## End-to-End Flow

```text
External System / PR2
        ↓
Shipment Integration
        ↓
Restock Order
        ↓
Delivery
        ↓
Tracking / GPS
        ↓
ETA & Monitoring
        ↓
Yard / Dock Scheduling
        ↓
Dock Assignment
        ↓
Dashboard
```

---

## PR2 Integration

PR2 or another backend can send shipment data using:

```http
POST https://e2-backend.onrender.com/integrations/shipments
```

The imported shipment becomes a normal E2 Delivery and can then be used by Tracking, ETA, Dock Operations, and Dashboard APIs.

See [integrations-api.md](integrations-api.md) for complete integration details.

---

## API Conventions

- No `/api/v1` prefix is currently used.
- No authentication is currently implemented.
- PostgreSQL is used as the database.
- Errors use FastAPI's standard `detail` response.
- List APIs currently do not use pagination.
- Live updates currently use HTTP polling instead of WebSockets.

For request bodies, responses, validation rules, errors, and integration details, see the individual API documentation files above.
