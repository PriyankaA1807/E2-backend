# Inventory API

The Inventory API manages stock information for products.

It is used to store and update the current stock and reserved stock associated with each Product.

**Base path:** `/inventory`

---

## Endpoints

| Method | Endpoint                  | Purpose                        |
| ------ | ------------------------- | ------------------------------ |
| GET    | `/inventory/`             | Get all inventory records      |
| GET    | `/inventory/{product_id}` | Get inventory for one Product  |
| POST   | `/inventory/`             | Create inventory for a Product |
| PUT    | `/inventory/{product_id}` | Update Product inventory       |

There is currently no Inventory delete endpoint.

---

# Inventory Object

An Inventory record contains stock information associated with one Product.

Typical fields are:

| Field            | Type     | Description                            |
| ---------------- | -------- | -------------------------------------- |
| `id`             | integer  | Database-generated inventory ID        |
| `product_id`     | integer  | Product associated with this inventory |
| `current_stock`  | integer  | Current stock quantity                 |
| `reserved_stock` | integer  | Quantity currently reserved            |
| `last_updated`   | datetime | Last inventory update time             |

Each Product is expected to have only one Inventory record.

---

# Create Inventory

## `POST /inventory/`

Creates inventory for an existing Product.

Unlike some other APIs, this endpoint currently receives its input through **query parameters**, not a JSON request body.

### Query Parameters

| Parameter        | Type    | Required | Default | Description                     |
| ---------------- | ------- | -------: | ------: | ------------------------------- |
| `product_id`     | integer |      Yes |       — | Product receiving the inventory |
| `current_stock`  | integer |       No |     `0` | Initial current stock           |
| `reserved_stock` | integer |       No |     `0` | Initial reserved stock          |

### Example Request

```http
POST /inventory/?product_id=1&current_stock=100&reserved_stock=10
```

---

## Backend Logic

Before creating the Inventory record, the backend performs two checks.

```text
Receive product_id
        ↓
Check Product exists
        ↓
Product missing?
   Yes → 404
        ↓ No
Check Inventory already exists
        ↓
Already exists?
   Yes → 400
        ↓ No
Create Inventory
        ↓
Commit to database
        ↓
Return Inventory
```

The Product must already exist because Inventory references a Product.

The backend also prevents multiple Inventory records from being created for the same Product.

---

## Product Not Found

**HTTP 404**

```json
{
  "detail": "Product not found"
}
```

---

## Inventory Already Exists

**HTTP 400**

```json
{
  "detail": "Inventory already exists for this product"
}
```

---

## Successful Response

The API returns the created Inventory record.

Example:

```json
{
  "id": 1,
  "product_id": 1,
  "current_stock": 100,
  "reserved_stock": 10,
  "last_updated": "2026-08-25T00:00:00"
}
```

---

# Get All Inventory

## `GET /inventory/`

Returns every Inventory record currently stored.

### Request

No request body or query parameter is required.

### Example Response

```json
[
  {
    "id": 1,
    "product_id": 1,
    "current_stock": 100,
    "reserved_stock": 10,
    "last_updated": "2026-08-25T00:00:00"
  },
  {
    "id": 2,
    "product_id": 2,
    "current_stock": 20,
    "reserved_stock": 5,
    "last_updated": "2026-08-25T00:05:00"
  }
]
```

The current endpoint does not implement pagination, filtering, or search.

---

# Get Inventory by Product

## `GET /inventory/{product_id}`

Returns the Inventory record associated with a Product.

### Path Parameter

| Parameter    | Type    | Required | Description                                   |
| ------------ | ------- | -------: | --------------------------------------------- |
| `product_id` | integer |      Yes | Product ID whose inventory should be returned |

Example:

```http
GET /inventory/1
```

### Important

The path parameter represents **Product ID**, not the Inventory row ID.

---

## Successful Response

```json
{
  "id": 1,
  "product_id": 1,
  "current_stock": 100,
  "reserved_stock": 10,
  "last_updated": "2026-08-25T00:00:00"
}
```

---

## Inventory Not Found

**HTTP 404**

```json
{
  "detail": "Inventory not found for this product"
}
```

---

# Update Inventory

## `PUT /inventory/{product_id}`

Updates the stock information for an existing Product Inventory record.

The values are currently supplied through query parameters.

### Path Parameter

| Parameter    | Type    | Required |
| ------------ | ------- | -------: |
| `product_id` | integer |      Yes |

### Query Parameters

| Parameter        | Type    | Required | Default |
| ---------------- | ------- | -------: | ------: |
| `current_stock`  | integer |      Yes |       — |
| `reserved_stock` | integer |       No |     `0` |

### Example Request

```http
PUT /inventory/1?current_stock=80&reserved_stock=5
```

---

## Backend Logic

```text
Find Inventory using product_id
        ↓
Inventory exists?
   No → 404
        ↓ Yes
Set current_stock
Set reserved_stock
        ↓
Update last_updated
        ↓
Commit changes
        ↓
Return updated Inventory
```

The endpoint updates the stock values stored for the Product.

---

## Successful Response

Example:

```json
{
  "id": 1,
  "product_id": 1,
  "current_stock": 80,
  "reserved_stock": 5,
  "last_updated": "2026-08-25T00:10:00"
}
```

---

## Inventory Not Found

**HTTP 404**

```json
{
  "detail": "Inventory not found for this product"
}
```

---

# How Inventory Connects to Other Modules

Inventory depends on Product.

```text
Product
   ↓
Inventory
```

The Product must exist before Inventory can be created.

Inventory information is also used by the Dashboard module.

The current dashboard considers an item low-stock when:

```text
current_stock <= product.reorder_level
```

For example:

```text
Product reorder level = 25
Current stock = 18

18 <= 25
    ↓
Low Stock
```

The current low-stock calculation uses `current_stock`.

It does not subtract `reserved_stock` before comparing against the reorder level.

---

# Frontend Integration

A typical Inventory screen can work like this:

```text
Page Load
   ↓
GET /inventory/
   ↓
Render Inventory Table
```

To create inventory:

```text
Select Product
     ↓
Enter current/reserved stock
     ↓
POST /inventory/
     ↓
Backend validates Product
     ↓
Inventory created
```

To edit stock:

```text
User edits stock
      ↓
PUT /inventory/{product_id}
      ↓
Updated stock returned
      ↓
Refresh row
```

For displaying Product names together with Inventory, the frontend may combine Inventory data with Product data from:

```http
GET /products/
```

because the Inventory record itself primarily references the Product through `product_id`.

---

# Error Handling

Frontend should handle:

| HTTP Status | Meaning                                 |
| ----------: | --------------------------------------- |
|       `200` | Successful read/update                  |
|       `400` | Inventory already exists for Product    |
|       `404` | Product or Inventory not found          |
|       `422` | Query/path parameter validation failure |

FastAPI errors normally use:

```json
{
  "detail": "..."
}
```

---

# Current Limitations

The current Inventory API does not implement:

* Delete Inventory
* Pagination
* Filtering
* Search
* Automatic Inventory creation when a Product is created
* Automatic RestockOrder creation when stock becomes low
* Authentication or authorization

The Dashboard can identify low-stock records, but low stock does **not automatically create a restock order** in the current backend.
