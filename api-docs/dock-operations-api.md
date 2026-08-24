# Dock Operations API

The Dock Operations API handles operational dock decisions for Deliveries.

It provides three main capabilities:

* Recommend suitable docks for a Delivery
* Assign a dock to a Delivery
* Reassign a Delivery from one dock to another

**Base path:** `/dock-operations`

---

## Endpoints

| Method | Endpoint                                   | Purpose                             |
| ------ | ------------------------------------------ | ----------------------------------- |
| GET    | `/dock-operations/recommend/{delivery_id}` | Get ranked dock recommendations     |
| POST   | `/dock-operations/assign/{delivery_id}`    | Assign a dock to a Delivery         |
| POST   | `/dock-operations/reassign/{delivery_id}`  | Reassign a Delivery to another dock |

---

# Overall Workflow

```text
Delivery
   ↓
GET /dock-operations/recommend/{delivery_id}
   ↓
Available docks are evaluated
   ↓
Docks receive scores
   ↓
Recommendations returned
   ↓
Operator selects Dock
   ↓
POST /dock-operations/assign/{delivery_id}
   ↓
Dock → reserved
Delivery → dock_id updated
```

The recommendation endpoint does **not automatically assign** the highest-scoring dock.

Recommendation and assignment are separate operations.

---

# Recommend Docks

## `GET /dock-operations/recommend/{delivery_id}`

Returns ranked Yard Dock recommendations for a Delivery.

### Path Parameter

| Parameter     | Type    | Required | Description               |
| ------------- | ------- | -------: | ------------------------- |
| `delivery_id` | integer |      Yes | Delivery requiring a dock |

### Example Request

```http
GET /dock-operations/recommend/2
```

---

# Backend Logic

The backend first retrieves the Delivery and available Yard Dock information.

Each Dock is evaluated using the current scoring rules.

Conceptually:

```text
Delivery
   ↓
Load Yard Docks
   ↓
Evaluate each Dock
   ↓
Calculate score
   ↓
Determine compatibility
   ↓
Sort by score
   ↓
Return ranked recommendations
```

---

# Current Dock Scoring Logic

The currently registered Dock Operations logic uses the following scoring rules.

### Dock is not available

If:

```text
dock.status != "available"
```

the Dock receives:

```text
score = 0
compatible = false
```

This prevents unavailable docks from being treated as suitable recommendations.

---

### Available Dock

An available Dock receives:

```text
+50 points
```

---

### Truck Support

If:

```text
supported_vehicle_type == "truck"
```

the Dock receives:

```text
+20 points
```

---

### Refrigerated Dock

If:

```text
refrigerated == true
```

the Dock receives:

```text
+10 points
```

---

### Standard Dock Type

If:

```text
dock_type == "standard"
```

the Dock receives:

```text
+10 points
```

---

# Example Scoring

Consider:

```text
Dock D-01

status = available
supported_vehicle_type = truck
refrigerated = true
dock_type = standard
```

Score:

```text
Available          +50
Truck support      +20
Refrigerated       +10
Standard type      +10
                   ───
Total               90
```

Another Dock:

```text
Dock D-02

status = available
supported_vehicle_type = truck
refrigerated = false
dock_type = standard
```

Score:

```text
Available          +50
Truck support      +20
Standard type      +10
                   ───
Total               80
```

Therefore:

```text
D-01 → 90
D-02 → 80
```

and D-01 appears before D-02 in the recommendation results.

---

# Recommendation Sorting

After scoring, the results are sorted by score in descending order.

```text
Highest Score
     ↓
Next Highest
     ↓
Next
     ↓
Lowest Score
```

This means the first recommendation is the highest-scoring Dock according to the current rules.

---

# Important Recommendation Behavior

The scoring function receives the Delivery object.

However, the **current registered scoring rules do not use shipment-specific Delivery fields to calculate the score**.

For example, the current scoring logic does not dynamically compare shipment-specific requirements such as:

```text
Delivery load requirement
Delivery vehicle length
Delivery refrigeration requirement
Delivery hazardous-load requirement
```

against Dock capabilities.

The recommendation is therefore currently based primarily on the Dock's own status and configured characteristics.

This is important for another team integrating the API: do not assume the recommendation is already performing full shipment-to-dock compatibility optimization.

---

# Recommendation Response

The endpoint returns ranked Dock recommendation information.

The response includes recommendation information such as:

```text
Dock
Score
Compatibility
Reasons
```

The integrating frontend should use the returned result rather than reproducing the scoring algorithm.

Conceptually:

```json
[
  {
    "dock_id": 1,
    "dock_number": "D-01",
    "score": 90,
    "compatible": true,
    "reasons": []
  },
  {
    "dock_id": 2,
    "dock_number": "D-02",
    "score": 80,
    "compatible": true,
    "reasons": []
  }
]
```

The exact response should be consumed according to the fields returned by the endpoint.

---

# Assign Dock

## `POST /dock-operations/assign/{delivery_id}`

Assigns a selected Yard Dock to a Delivery.

### Path Parameter

| Parameter     | Type    | Required |
| ------------- | ------- | -------: |
| `delivery_id` | integer |      Yes |

### Request Body

```json
{
  "dock_id": 3
}
```

### Request Field

| Field     | Type    | Required | Description         |
| --------- | ------- | -------: | ------------------- |
| `dock_id` | integer |      Yes | Yard Dock to assign |

---

# Assignment Validation

Before assignment, the backend checks:

```text
Delivery exists?
      ↓
No → HTTP 404
      ↓
Yes
      ↓
Dock exists?
      ↓
No → HTTP 404
      ↓
Yes
      ↓
Dock available?
      ↓
No → Assignment rejected
      ↓
Yes
      ↓
Assign Dock
```

Only a Dock whose status is:

```text
available
```

can be assigned through this operation.

---

# Assignment Side Effects

Dock assignment changes both the Delivery and Yard Dock state.

```text
Selected Dock
     ↓
status = reserved

Delivery
     ↓
dock_id = selected Dock ID
```

Conceptually:

```text
Delivery 2
+
Dock 3 (available)
       ↓
ASSIGN
       ↓
Delivery 2.dock_id = 3
Dock 3.status = reserved
```

These changes are committed together by the backend.

---

# Existing Dock Assignment

If the Delivery already has another Dock assigned, the current assignment logic releases the old Dock.

```text
Delivery
   ↓
Old Dock = D-01
   ↓
Assign D-03
   ↓
D-01 → available
D-03 → reserved
Delivery.dock_id → D-03
```

This prevents the previous Dock from remaining reserved after the Delivery moves to another Dock.

---

# Reassign Dock

## `POST /dock-operations/reassign/{delivery_id}`

Moves a Delivery from its current Dock to another available Dock.

### Request Body

```json
{
  "dock_id": 4
}
```

The new Dock must exist and must be available.

---

# Reassignment Flow

```text
Delivery
   ↓
Current Dock
   ↓
Release Current Dock
   ↓
current dock.status = available
   ↓
Reserve New Dock
   ↓
new dock.status = reserved
   ↓
Update Delivery.dock_id
   ↓
Commit
```

Example:

```text
Before

Delivery 2 → Dock D-01

D-01 = reserved
D-03 = available


Reassign to D-03


After

Delivery 2 → Dock D-03

D-01 = available
D-03 = reserved
```

---

# How This Connects to Yard Docks

The Yard Docks API manages Dock records:

```text
/yard-docks
```

The Dock Operations API uses those records to perform operational decisions:

```text
/dock-operations
```

Therefore:

```text
Yard Docks
    ↓
Dock Configuration
    ↓
Dock Operations
    ├── Recommend
    ├── Assign
    └── Reassign
```

A frontend should not manually reproduce assignment logic by separately changing a Dock and Delivery.

Use the Dock Operations endpoints so the backend can update both sides consistently.

---

# How This Connects to Delivery

The relationship is stored through:

```text
Delivery.dock_id
```

Before assignment:

```text
delivery.dock_id = null
```

After assignment:

```text
delivery.dock_id = 3
```

The selected Dock simultaneously becomes:

```text
reserved
```

---

# Relationship with Operations & Alerts

The Operations module checks for situations where a shipment has reached the yard but has no Dock assigned.

Current exception logic includes:

```text
Delivery status = arrived/unloading
        +
dock_id is missing
        ↓
Shipment Exception
```

Therefore Dock assignment is not only a UI operation; it also affects operational exception detection.

---

# Frontend Integration

A shipment approaching the yard can use:

```text
Shipment Detail
      ↓
GET /dock-operations/recommend/{delivery_id}
      ↓
Receive ranked Docks
      ↓
Display Recommendations
```

Example UI:

```text
Recommended Docks

D-01
Score: 90
Compatible

D-02
Score: 80
Compatible
```

The operator selects a Dock:

```text
Select D-01
     ↓
POST /dock-operations/assign/{delivery_id}
     ↓
{
  "dock_id": 1
}
     ↓
Dock reserved
     ↓
Delivery updated
```

---

# Reassignment UI

If the operator needs to move the shipment:

```text
Current Dock: D-01
       ↓
Choose New Dock: D-03
       ↓
POST /dock-operations/reassign/{delivery_id}
       ↓
D-01 released
D-03 reserved
Delivery updated
```

---

# Cross-Team Integration

Another frontend or service only needs to understand the API contract.

It should **not copy the scoring algorithm into its own application**.

Recommended pattern:

```text
Need Dock
   ↓
Call Recommendation API
   ↓
Use returned ranking
   ↓
User/system selects Dock
   ↓
Call Assignment API
```

This keeps Dock decision logic inside the E2 backend.

If the scoring logic changes later, other applications can continue consuming the same API without reimplementing the algorithm.

---

# Important Router Note

The repository also contains:

```text
app/routers/dock_recommendation.py
```

with separate recommendation logic.

However, that router is **not currently registered in `main.py`**.

Therefore another application should not currently integrate against:

```text
/dock-recommendation/
```

The currently exposed Dock recommendation interface is:

```http
GET /dock-operations/recommend/{delivery_id}
```

This documentation describes the registered Dock Operations API.

---

# Error Handling

Integrating applications should handle:

| HTTP Status | Meaning                                        |
| ----------: | ---------------------------------------------- |
|       `200` | Recommendation/assignment operation successful |
|       `400` | Dock cannot be assigned in its current state   |
|       `404` | Delivery or Yard Dock not found                |
|       `422` | Request/path/body validation failure           |

FastAPI errors use:

```json
{
  "detail": "Error message"
}
```

---

# Current Limitations

The current Dock Operations API does not provide:

* Full shipment-specific compatibility scoring
* Automatic assignment of the highest-scoring Dock
* Automatic Dock assignment when a Delivery arrives
* Authentication/authorization

The current recommendation score is based on the implemented Dock rules.

Recommendation and assignment remain separate operations:

```text
Recommend
    ↓
Select
    ↓
Assign
```

This allows the frontend/operator to review the recommendation before committing a Dock assignment.
