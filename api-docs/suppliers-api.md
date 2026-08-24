# Suppliers API

The Suppliers API manages supplier master data used when creating Restock Orders.

**Base path:** `/suppliers`

---

## Endpoints

| Method | Endpoint                   | Purpose           |
| ------ | -------------------------- | ----------------- |
| GET    | `/suppliers/`              | Get all suppliers |
| GET    | `/suppliers/{supplier_id}` | Get one supplier  |
| POST   | `/suppliers/`              | Create a supplier |
| PUT    | `/suppliers/{supplier_id}` | Update a supplier |
| DELETE | `/suppliers/{supplier_id}` | Delete a supplier |

---

# Supplier Object

A Supplier contains:

| Field            | Type          | Description                    |
| ---------------- | ------------- | ------------------------------ |
| `id`             | integer       | Database-generated supplier ID |
| `name`           | string        | Supplier name                  |
| `contact_person` | string / null | Main contact person            |
| `email`          | string / null | Supplier email                 |
| `phone`          | string / null | Supplier phone                 |
| `address`        | string / null | Supplier address               |

---

# Create Supplier

## `POST /suppliers/`

Creates a new Supplier.

The current implementation receives values as **query parameters**, not a JSON request body.

### Query Parameters

| Parameter        | Type          | Required |
| ---------------- | ------------- | -------: |
| `name`           | string        |      Yes |
| `contact_person` | string / null |       No |
| `email`          | string / null |       No |
| `phone`          | string / null |       No |
| `address`        | string / null |       No |

### Example Request

```http
POST /suppliers/?name=ABC%20Logistics&contact_person=Rahul&email=ops@example.com&phone=9876543210
```

---

## Backend Logic

```text
Receive supplier details
        ↓
Create Supplier object
        ↓
Add to database session
        ↓
Commit
        ↓
Refresh
        ↓
Return Supplier
```

The current create route does not perform a uniqueness check on supplier name, email, or phone.

---

## Successful Response

Example:

```json
{
  "id": 1,
  "name": "ABC Logistics",
  "contact_person": "Rahul",
  "email": "ops@example.com",
  "phone": "9876543210",
  "address": null
}
```

---

# Get All Suppliers

## `GET /suppliers/`

Returns all Supplier records.

### Request

No body or query parameters are required.

### Example Response

```json
[
  {
    "id": 1,
    "name": "ABC Logistics",
    "contact_person": "Rahul",
    "email": "ops@example.com",
    "phone": "9876543210",
    "address": null
  },
  {
    "id": 2,
    "name": "XYZ Supply Co.",
    "contact_person": "Anita",
    "email": "contact@xyz.com",
    "phone": null,
    "address": "Kolkata"
  }
]
```

The current endpoint does not implement pagination, filtering, sorting, or search.

---

# Get Supplier by ID

## `GET /suppliers/{supplier_id}`

Returns one Supplier using its database ID.

### Path Parameter

| Parameter     | Type    | Required | Description          |
| ------------- | ------- | -------: | -------------------- |
| `supplier_id` | integer |      Yes | Supplier database ID |

Example:

```http
GET /suppliers/1
```

### Successful Response

```json
{
  "id": 1,
  "name": "ABC Logistics",
  "contact_person": "Rahul",
  "email": "ops@example.com",
  "phone": "9876543210",
  "address": null
}
```

### Supplier Not Found

**HTTP 404**

```json
{
  "detail": "Supplier not found"
}
```

---

# Update Supplier

## `PUT /suppliers/{supplier_id}`

Updates an existing Supplier.

The current implementation receives update values through query parameters.

### Path Parameter

| Parameter     | Type    | Required |
| ------------- | ------- | -------: |
| `supplier_id` | integer |      Yes |

### Query Parameters

| Parameter        | Type          | Required |
| ---------------- | ------------- | -------: |
| `name`           | string        |      Yes |
| `contact_person` | string / null |       No |
| `email`          | string / null |       No |
| `phone`          | string / null |       No |
| `address`        | string / null |       No |

### Example Request

```http
PUT /suppliers/1?name=ABC%20Logistics%20Pvt%20Ltd&email=new@example.com
```

---

## Backend Logic

```text
Find Supplier by ID
       ↓
Supplier exists?
  No → 404
       ↓ Yes
Update supplier fields
       ↓
Commit
       ↓
Refresh
       ↓
Return updated Supplier
```

---

## Successful Response

Example:

```json
{
  "id": 1,
  "name": "ABC Logistics Pvt Ltd",
  "contact_person": null,
  "email": "new@example.com",
  "phone": null,
  "address": null
}
```

### Important Update Behavior

The current update handler accepts `name` as required.

Optional values that are not supplied can be passed through as `null` by the current route behavior.

A frontend should therefore send all Supplier values it wants to preserve when using this update endpoint.

---

# Delete Supplier

## `DELETE /suppliers/{supplier_id}`

Deletes a Supplier by ID.

### Path Parameter

| Parameter     | Type    | Required |
| ------------- | ------- | -------: |
| `supplier_id` | integer |      Yes |

Example:

```http
DELETE /suppliers/1
```

### Backend Logic

```text
Find Supplier
     ↓
Exists?
 No → 404
     ↓ Yes
Delete Supplier
     ↓
Commit
     ↓
Return success message
```

### Successful Response

```json
{
  "message": "Supplier deleted successfully"
}
```

### Supplier Not Found

```json
{
  "detail": "Supplier not found"
}
```

---

# How Suppliers Connect to Other Modules

Suppliers are used by Restock Orders.

```text
Supplier
   │
   └──────────────┐
                  ↓
Product ─────→ Restock Order
```

When a Restock Order is created, the backend validates that the referenced Supplier exists.

Therefore the normal integration order is:

```text
Create Supplier
      ↓
Create / Select Product
      ↓
Create Restock Order
```

---

# Frontend Integration

A Supplier Management page can use:

```text
Page Load
   ↓
GET /suppliers/
   ↓
Render Supplier Table
```

Create Supplier:

```text
Supplier Form
    ↓
POST /suppliers/
    ↓
Supplier created
    ↓
Refresh list
```

Edit Supplier:

```text
Edit Form
   ↓
PUT /suppliers/{supplier_id}
   ↓
Updated Supplier
   ↓
Refresh row
```

Delete Supplier:

```text
Delete action
    ↓
DELETE /suppliers/{supplier_id}
    ↓
Success
    ↓
Refresh list
```

On the Restock Order screen, suppliers can be loaded using:

```http
GET /suppliers/
```

and displayed in a selector.

The frontend should normally submit the selected Supplier's `id` as `supplier_id` when creating a Restock Order.

---

# Error Handling

Frontend should handle:

| HTTP Status | Meaning                      |
| ----------: | ---------------------------- |
|       `200` | Successful request           |
|       `404` | Supplier not found           |
|       `422` | Invalid path/query parameter |

FastAPI HTTP errors use:

```json
{
  "detail": "..."
}
```

---

# Current Limitations

The current Suppliers API does not implement:

* Supplier search
* Pagination
* Sorting
* Filtering
* Supplier uniqueness validation
* Separate PATCH/partial-update endpoint
* Authentication/authorization
