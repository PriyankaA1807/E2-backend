# Products API

The Products API manages product master data used by inventory and restock-order workflows.

**Base path:** `/products`

---

## Endpoints

| Method | Endpoint                 | Purpose          |
| ------ | ------------------------ | ---------------- |
| POST   | `/products/`             | Create a product |
| GET    | `/products/`             | Get all products |
| GET    | `/products/{product_id}` | Get one product  |
| DELETE | `/products/{product_id}` | Delete a product |

There is currently **no product update endpoint**.

---

# Product Object

A Product contains:

| Field           | Type          | Description                           |
| --------------- | ------------- | ------------------------------------- |
| `id`            | integer       | Database-generated product ID         |
| `sku`           | string        | Unique product SKU                    |
| `name`          | string        | Product name                          |
| `category`      | string / null | Product category                      |
| `unit_price`    | float / null  | Product price                         |
| `reorder_level` | integer       | Stock level used for low-stock checks |

---

# Create Product

## `POST /products/`

Creates a new Product.

### Request

**Content-Type:** `application/json`

```json
{
  "sku": "SKU-001",
  "name": "Industrial Bearing",
  "category": "Mechanical",
  "unit_price": 450.5,
  "reorder_level": 25
}
```

### Request Fields

| Field           | Type          | Required | Default |
| --------------- | ------------- | -------: | ------- |
| `sku`           | string        |      Yes | —       |
| `name`          | string        |      Yes | —       |
| `category`      | string / null |       No | `null`  |
| `unit_price`    | float / null  |       No | `null`  |
| `reorder_level` | integer       |       No | `0`     |

---

## Backend Logic

Before inserting the Product, the backend checks whether another Product already uses the same SKU.

Flow:

```text
Receive ProductCreate
        ↓
Search Product by SKU
        ↓
SKU already exists?
   ┌────┴────┐
  Yes       No
   ↓         ↓
HTTP 400   Create Product
             ↓
           Commit
             ↓
           Refresh
             ↓
           Return Product
```

This prevents duplicate SKUs.

---

## Successful Response

Returns the created Product.

Example:

```json
{
  "id": 1,
  "sku": "SKU-001",
  "name": "Industrial Bearing",
  "category": "Mechanical",
  "unit_price": 450.5,
  "reorder_level": 25
}
```

---

## Duplicate SKU

**HTTP 400**

```json
{
  "detail": "Product with this SKU already exists"
}
```

---

# Get All Products

## `GET /products/`

Returns all Product records.

### Request

No body or query parameters are required.

### Example Response

```json
[
  {
    "id": 1,
    "sku": "SKU-001",
    "name": "Industrial Bearing",
    "category": "Mechanical",
    "unit_price": 450.5,
    "reorder_level": 25
  },
  {
    "id": 2,
    "sku": "SKU-002",
    "name": "Hydraulic Pump",
    "category": "Industrial",
    "unit_price": 1200.0,
    "reorder_level": 10
  }
]
```

### Current Behavior

The endpoint currently returns all Products.

There is no pagination, search, sorting, or filtering implemented in this route.

---

# Get Product by ID

## `GET /products/{product_id}`

Returns one Product using its database ID.

### Path Parameter

| Parameter    | Type    | Required | Description         |
| ------------ | ------- | -------: | ------------------- |
| `product_id` | integer |      Yes | Product database ID |

Example:

```http
GET /products/1
```

### Successful Response

```json
{
  "id": 1,
  "sku": "SKU-001",
  "name": "Industrial Bearing",
  "category": "Mechanical",
  "unit_price": 450.5,
  "reorder_level": 25
}
```

### Product Not Found

**HTTP 404**

```json
{
  "detail": "Product not found"
}
```

---

# Delete Product

## `DELETE /products/{product_id}`

Deletes a Product by ID.

### Path Parameter

| Parameter    | Type    | Required |
| ------------ | ------- | -------: |
| `product_id` | integer |      Yes |

Example:

```http
DELETE /products/1
```

### Backend Logic

```text
Find Product
     ↓
Exists?
 ┌───┴────┐
No       Yes
↓          ↓
404      Delete
           ↓
         Commit
           ↓
      Success message
```

### Successful Response

```json
{
  "message": "Product deleted successfully"
}
```

### Product Not Found

**HTTP 404**

```json
{
  "detail": "Product not found"
}
```

---

# Frontend Integration

A Products page can use:

```text
Page Load
   ↓
GET /products/
   ↓
Render Product Table
```

Create Product:

```text
Product Form
    ↓
POST /products/
    ↓
Backend validates SKU
    ↓
Product created
    ↓
Refresh product list
```

Delete Product:

```text
Delete button
    ↓
DELETE /products/{product_id}
    ↓
Success
    ↓
Remove/refresh product row
```

Products are also useful as selectable values when creating Restock Orders.

---

# Error Handling

Frontend should handle at least:

| HTTP Status | Meaning                          |
| ----------: | -------------------------------- |
|       `200` | Successful read/delete operation |
|       `400` | Duplicate SKU                    |
|       `404` | Product does not exist           |
|       `422` | Request body validation failed   |

FastAPI errors normally use:

```json
{
  "detail": "..."
}
```

---

# Current Limitations

The current Products API does not implement:

* Product update (`PUT` / `PATCH`)
* Pagination
* Search
* Filtering
* Sorting
* Authentication/authorization

These should not be assumed by the frontend.
