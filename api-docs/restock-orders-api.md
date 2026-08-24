# Restock Orders API

The Restock Orders API manages procurement/restocking requests for Products.

A Restock Order connects a **Product** with a **Supplier**, specifies the required quantity, tracks the order status, and can store an expected delivery time.

**Base path:** `/restock-orders`

---

## Endpoints

| Method | Endpoint                            | Purpose                     |
| ------ | ----------------------------------- | --------------------------- |
| POST   | `/restock-orders/`                  | Create a Restock Order      |
| GET    | `/restock-orders/`                  | Get all Restock Orders      |
| GET    | `/restock-orders/{order_id}`        | Get one Restock Order       |
| PUT    | `/restock-orders/{order_id}/status` | Update Restock Order status |
| DELETE | `/restock-orders/{order_id}`        | Delete a Restock Order      |

---

# Restock Order Object

A Restock Order contains:

| Field               | Type            | Description                         |
| ------------------- | --------------- | ----------------------------------- |
| `id`                | integer         | Database-generated Restock Order ID |
| `product_id`        | integer         | Product being ordered               |
| `supplier_id`       | integer         | Supplier providing the Product      |
| `quantity`          | integer         | Quantity requested                  |
| `status`            | string          | Current Restock Order status        |
| `order_date`        | datetime        | Time the Restock Order was created  |
| `expected_delivery` | datetime / null | Expected delivery time              |

---

# Create Restock Order

## `POST /restock-orders/`

Creates a new Restock Order.

Before creating the order, both the Product and Supplier must already exist.

### Request

**Content-Type:** `application/json`

### Example Body

```json
{
  "product_id": 1,
  "supplier_id": 2,
  "quantity": 100,
  "status": "pending",
  "expected_delivery": "2026-08-30T12:00:00"
}
```

---

## Request Fields

| Field               | Type            | Required | Default     | Description                   |
| ------------------- | --------------- | -------: | ----------- | ----------------------------- |
| `product_id`        | integer         |      Yes | —           | Product being restocked       |
| `supplier_id`       | integer         |      Yes | —           | Supplier fulfilling the order |
| `quantity`          | integer         |      Yes | —           | Quantity requested            |
| `status`            | string          |       No | `"pending"` | Initial order status          |
| `expected_delivery` | datetime / null |       No | `null`      | Expected delivery timestamp   |

Timestamps are represented as ISO-style datetime values.

---

# Backend Validation

Before creating the Restock Order, the backend validates the relationships and quantity.

```text
Receive Restock Order
        ↓
Check Product
        ↓
Product exists?
 No → HTTP 404
        ↓ Yes
Check Supplier
        ↓
Supplier exists?
 No → HTTP 404
        ↓ Yes
Check quantity
        ↓
quantity > 0?
 No → HTTP 400
        ↓ Yes
Create Restock Order
        ↓
Commit
        ↓
Return created order
```

---

## Product Not Found

**HTTP 404**

```json
{
  "detail": "Product not found"
}
```

---

## Supplier Not Found

**HTTP 404**

```json
{
  "detail": "Supplier not found"
}
```

---

## Invalid Quantity

The quantity must be greater than zero.

**HTTP 400**

```json
{
  "detail": "Quantity must be greater than 0"
}
```

---

# Successful Response

The API returns the created Restock Order.

Example:

```json
{
  "id": 1,
  "product_id": 1,
  "supplier_id": 2,
  "quantity": 100,
  "status": "pending",
  "order_date": "2026-08-24T20:10:00",
  "expected_delivery": "2026-08-30T12:00:00"
}
```

---

# Get All Restock Orders

## `GET /restock-orders/`

Returns all Restock Orders stored in the system.

### Request

No body or query parameters are required.

### Example Response

```json
[
  {
    "id": 1,
    "product_id": 1,
    "supplier_id": 2,
    "quantity": 100,
    "status": "pending",
    "order_date": "2026-08-24T20:10:00",
    "expected_delivery": "2026-08-30T12:00:00"
  },
  {
    "id": 2,
    "product_id": 3,
    "supplier_id": 1,
    "quantity": 50,
    "status": "approved",
    "order_date": "2026-08-24T20:20:00",
    "expected_delivery": "2026-09-01T10:00:00"
  }
]
```

The current endpoint does not implement pagination, filtering, search, or sorting parameters.

---

# Get Restock Order by ID

## `GET /restock-orders/{order_id}`

Returns one Restock Order.

### Path Parameter

| Parameter  | Type    | Required | Description               |
| ---------- | ------- | -------: | ------------------------- |
| `order_id` | integer |      Yes | Restock Order database ID |

Example:

```http
GET /restock-orders/1
```

---

## Successful Response

```json
{
  "id": 1,
  "product_id": 1,
  "supplier_id": 2,
  "quantity": 100,
  "status": "pending",
  "order_date": "2026-08-24T20:10:00",
  "expected_delivery": "2026-08-30T12:00:00"
}
```

---

## Restock Order Not Found

**HTTP 404**

```json
{
  "detail": "Restock order not found"
}
```

---

# Update Restock Order Status

## `PUT /restock-orders/{order_id}/status`

Updates the `status` field of an existing Restock Order.

The status is currently supplied as a **query parameter**.

### Path Parameter

| Parameter  | Type    | Required |
| ---------- | ------- | -------: |
| `order_id` | integer |      Yes |

### Query Parameter

| Parameter | Type   | Required | Description              |
| --------- | ------ | -------: | ------------------------ |
| `status`  | string |      Yes | New Restock Order status |

### Example Request

```http
PUT /restock-orders/1/status?status=approved
```

---

# Backend Logic

```text
Find Restock Order
        ↓
Order exists?
 No → HTTP 404
        ↓ Yes
Set order.status
        ↓
Commit
        ↓
Return updated status
```

---

## Successful Response

```json
{
  "message": "Restock order status updated successfully",
  "order_id": 1,
  "status": "approved"
}
```

---

## Important Status Behavior

The current endpoint accepts a string for the Restock Order status.

It does **not currently enforce a fixed Restock Order status enum or transition state machine**.

For example, the backend does not currently enforce a sequence such as:

```text
pending
   ↓
approved
   ↓
completed
```

Therefore, another service or frontend integrating this endpoint should only send status values agreed upon by the project team.

The Dashboard currently specifically checks for:

```text
status == "pending"
```

when calculating pending Restock Orders.

---

# Delete Restock Order

## `DELETE /restock-orders/{order_id}`

Deletes a Restock Order.

### Path Parameter

| Parameter  | Type    | Required |
| ---------- | ------- | -------: |
| `order_id` | integer |      Yes |

Example:

```http
DELETE /restock-orders/1
```

---

## Backend Logic

```text
Find Restock Order
        ↓
Exists?
 No → HTTP 404
        ↓ Yes
Delete
        ↓
Commit
        ↓
Return success message
```

---

## Successful Response

```json
{
  "message": "Restock order deleted successfully"
}
```

---

# How Restock Orders Connect to Other Modules

Restock Orders sit between procurement data and shipment data.

```text
Product ──────┐
              │
              ▼
        Restock Order
              ▲
              │
Supplier ─────┘
              │
              ▼
           Delivery
```

A Product and Supplier must already exist before the Restock Order can be created.

A Delivery later references the Restock Order through:

```text
restock_order_id
```

The Delivery API validates that the referenced Restock Order exists before creating a shipment.

Therefore, the normal integration flow is:

```text
Product
   +
Supplier
   ↓
Restock Order
   ↓
Delivery
   ↓
Tracking
```

---

# Frontend Integration

A Restock Orders screen can load:

```http
GET /restock-orders/
```

to display the existing procurement requests.

For creating a Restock Order, the frontend can first retrieve:

```http
GET /products/
```

and:

```http
GET /suppliers/
```

Then display both as selectors.

Example UI flow:

```text
Select Product
      +
Select Supplier
      +
Enter Quantity
      +
Expected Delivery
      ↓
POST /restock-orders/
      ↓
Backend validates references
      ↓
Restock Order created
```

When creating a Delivery later, use the Restock Order's `id` as the shipment's `restock_order_id`.

---

# Cross-Team Integration Notes

A service integrating with this API should understand that `product_id` and `supplier_id` are **references to existing records**, not names.

Correct:

```json
{
  "product_id": 1,
  "supplier_id": 2,
  "quantity": 100
}
```

Do not send:

```json
{
  "product": "Industrial Bearing",
  "supplier": "ABC Logistics",
  "quantity": 100
}
```

unless the backend contract is changed.

The receiving service should first obtain the relevant IDs from the Product and Supplier APIs.

---

# Error Handling

| HTTP Status | Meaning                                       |
| ----------: | --------------------------------------------- |
|       `200` | Successful read/update/delete                 |
|       `400` | Invalid business input such as quantity ≤ 0   |
|       `404` | Product, Supplier, or Restock Order not found |
|       `422` | Request/query/path validation failure         |

FastAPI HTTP errors normally follow:

```json
{
  "detail": "Error message"
}
```

---

# Current Limitations

The current Restock Orders API does not implement:

* Automatic Restock Order creation from low-stock detection
* Fixed Restock Order status enum
* Strict status transition rules
* Full Restock Order edit/update endpoint
* Pagination
* Search/filtering
* Authentication/authorization

Creating a Restock Order also does **not automatically create a Delivery**. Delivery creation is a separate API operation.
