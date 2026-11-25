# API Endpoints & Database Schemas (MVP)

> **Architectural Style:** RESTful JSON API over HTTPS (`NFR_01`) with Layered ECB Backend (`Controllers` → `Services` → `Repositories`).

---

## 1. Database Schemas (`PostgreSQL`)

Aligned with our UML Domain Class Diagram and `Modular-Design.md` specifications.

### 1.1 `Users`
Stores authenticated platform staff (`COURIER`, `ADMIN`). *(Note: Recipients are guest-only in the MVP and do not require an account.)*

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `user_id` | `UUID` | `PRIMARY KEY` | Unique internal user identifier |
| `name` | `VARCHAR(100)` | `NOT NULL` | Full name of staff member |
| `email` | `VARCHAR(255)` | `UNIQUE, NOT NULL` | Login email (`SK`) |
| `password_hash` | `VARCHAR(255)` | `NOT NULL` | Bcrypt/Argon2 hashed password |
| `role` | `VARCHAR(20)` | `NOT NULL` | Enum: `COURIER`, `ADMIN` |
| `company_name` | `VARCHAR(100)` | `NULLABLE` | Carrier company (applicable when `role = COURIER`) |
| `created_at` | `TIMESTAMP` | `DEFAULT NOW()` | Account creation timestamp |

---

### 1.2 `Lockers`
Represents physical locker stations deployed across sites.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `locker_id` | `UUID` | `PRIMARY KEY` | Unique locker station identifier |
| `name` | `VARCHAR(100)` | `NOT NULL` | Station display name (e.g., "Belval Plaza Station") |
| `address` | `VARCHAR(255)` | `NOT NULL` | Physical street address |
| `gps_location` | `VARCHAR(100)` | `NOT NULL` | Latitude/Longitude coordinates |
| `opening_hours` | `VARCHAR(100)` | `NOT NULL` | Site accessibility hours (e.g., `"08:00 - 22:00"` or `"24/7"`) |
| `operational_status` | `VARCHAR(20)` | `DEFAULT 'ONLINE'` | Enum: `ONLINE`, `OFFLINE`, `MAINTENANCE` |
| `instructions` | `TEXT` | `NULLABLE` | On-site navigation or access notes |

---

### 1.3 `Compartments`
Individual physical boxes belonging to a `Locker` station.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `compartment_id` | `UUID` | `PRIMARY KEY` | Unique compartment identifier |
| `locker_id` | `UUID` | `FK -> Lockers.locker_id, NOT NULL` | Parent locker station |
| `compartment_number` | `INT` | `NOT NULL` | Physical box label on the kiosk (e.g., `1`, `2`, `14`) |
| `size_category` | `VARCHAR(10)` | `NOT NULL` | Enum: `SMALL`, `MEDIUM`, `LARGE` |
| `status` | `VARCHAR(20)` | `DEFAULT 'AVAILABLE'` | Enum: `AVAILABLE`, `RESERVED`, `OCCUPIED`, `MAINTENANCE` |
| `version` | `INT` | `DEFAULT 0` | Optimistic locking version for atomic concurrency (`NFR_04` / `NFR_08`) |

---

### 1.4 `Parcels`
Core shipment entity tracking lifecycle state, locker assignment, and guest recipient contact.

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `parcel_id` | `UUID` | `PRIMARY KEY` | Internal ID generated from hash of tracking barcode |
| `tracking_number` | `VARCHAR(100)` | `UNIQUE, NOT NULL` | External barcode / carrier tracking ID (`SK`) |
| `size_category` | `VARCHAR(10)` | `NOT NULL` | Enum: `SMALL`, `MEDIUM`, `LARGE` |
| `status` | `VARCHAR(30)` | `NOT NULL` | Enum: `REGISTERED`, `ASSIGNED`, `READY_FOR_PICKUP`, `COLLECTED`, `EXPIRED` |
| `preferred_locker_id` | `UUID` | `FK -> Lockers.locker_id, NULLABLE` | Recipient's preferred station from checkout |
| `compartment_id` | `UUID` | `FK -> Compartments.compartment_id, NULLABLE` | Assigned/occupied compartment |
| `registered_by_courier_id` | `UUID` | `FK -> Users.user_id, NOT NULL` | Courier who registered the parcel |
| `recipient_contact` | `VARCHAR(255)` | `NOT NULL` | Guest recipient email or phone number |
| `notes` | `TEXT` | `NULLABLE` | Optional handling instructions |
| `expected_delivery` | `TIMESTAMP` | `NULLABLE` | Estimated arrival timestamp |
| `registered_at` | `TIMESTAMP` | `DEFAULT NOW()` | Registration timestamp |
| `deposited_at` | `TIMESTAMP` | `NULLABLE` | Physical drop-off timestamp |
| `pickup_deadline` | `TIMESTAMP` | `NULLABLE` | Computed as `deposited_at + 7 days` |
| `collected_at` | `TIMESTAMP` | `NULLABLE` | Recipient pickup timestamp |

---

### 1.5 `PickupCodes`
Single-use credentials generated upon physical deposit and verified at the terminal (`NFR_02`).

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `code_id` | `UUID` | `PRIMARY KEY` | Unique credential identifier |
| `parcel_id` | `UUID` | `FK -> Parcels.parcel_id, UNIQUE, NOT NULL` | Associated parcel |
| `code_hash` | `VARCHAR(255)` | `NOT NULL` | Hashed 6-digit PIN / QR token |
| `failed_attempts` | `INT` | `DEFAULT 0` | Counter for brute-force protection (locks at `5`) |
| `locked_until` | `TIMESTAMP` | `NULLABLE` | 15-minute lockout expiration (`NFR_02`) |
| `issued_at` | `TIMESTAMP` | `DEFAULT NOW()` | Generation timestamp |
| `expires_at` | `TIMESTAMP` | `NOT NULL` | Matches `Parcels.pickup_deadline` |
| `used_at` | `TIMESTAMP` | `NULLABLE` | Populated upon collection to invalidate code |

---

## 2. REST API Endpoints

### 2.1 Authentication (`AuthController`)

#### `POST /api/auth/login`
Authenticates a Courier or Administrator and returns a signed JWT (`NFR_01`).
* **Access:** Public
* **Request Body:**
```json
{
  "email": "courier@post.lu",
  "password": "securePassword123"
}
```
* **Response (`200 OK`):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "userId": "u-101",
    "name": "Alex Meyer",
    "role": "COURIER"
  }
}
```
* **Errors:** `401 Unauthorized` (invalid credentials)

---

### 2.2 Parcel Registration — UC1 (`RegistrationController`)

#### `POST /api/parcels`
Registers an incoming parcel in the system with status `REGISTERED`.
* **Access:** `COURIER` (`Bearer JWT`)
* **Request Body:**
```json
{
  "trackingNumber": "LU-987654321",
  "sizeCategory": "MEDIUM",
  "preferredLockerId": "loc-belval-01",
  "recipientContact": "recipient@example.lu",
  "expectedDelivery": "2026-11-20T14:00:00Z",
  "notes": "Handle with care"
}
```
* **Response (`201 Created`):**
```json
{
  "parcelId": "p-7a8b9c0d",
  "trackingNumber": "LU-987654321",
  "status": "REGISTERED",
  "preferredLockerId": "loc-belval-01",
  "registeredAt": "2026-11-19T15:10:00Z"
}
```
* **Errors:** `400 Bad Request` (validation error), `409 Conflict` (duplicate `trackingNumber`)

#### `GET /api/parcels?status=REGISTERED`
Retrieves the courier's registered parcels awaiting compartment assignment.
* **Access:** `COURIER` (`Bearer JWT`)
* **Response (`200 OK`):**
```json
[
  {
    "parcelId": "p-7a8b9c0d",
    "trackingNumber": "LU-987654321",
    "sizeCategory": "MEDIUM",
    "status": "REGISTERED",
    "preferredLockerId": "loc-belval-01",
    "expectedDelivery": "2026-11-20T14:00:00Z"
  }
]
```

---

### 2.3 Compartment Assignment — UC2 (`AssignmentController`)

#### `GET /api/lockers/{lockerId}/compartments?size=MEDIUM`
Lists available compartments at a locker station and identifies the smallest fitting recommendation.
* **Access:** `COURIER` (`Bearer JWT`)
* **Response (`200 OK`):**
```json
{
  "lockerId": "loc-belval-01",
  "recommendedCompartmentId": "comp-04",
  "availableCompartments": [
    { "compartmentId": "comp-04", "compartmentNumber": 4, "sizeCategory": "MEDIUM" },
    { "compartmentId": "comp-09", "compartmentNumber": 9, "sizeCategory": "LARGE" }
  ]
}
```

#### `POST /api/parcels/{parcelId}/assign`
Atomically reserves a compartment (`RESERVED`) and updates the parcel to `ASSIGNED`.
* **Access:** `COURIER` (`Bearer JWT`)
* **Request Body:**
```json
{
  "lockerId": "loc-belval-01",
  "compartmentId": "comp-04"
}
```
* **Response (`200 OK`):**
```json
{
  "parcelId": "p-7a8b9c0d",
  "status": "ASSIGNED",
  "lockerId": "loc-belval-01",
  "compartmentId": "comp-04",
  "compartmentNumber": 4
}
```
* **Errors:** `404 Not Found` (parcel/locker not found), `409 Conflict` (compartment already reserved by another courier)

---

### 2.4 Physical Terminal Deposit — UC3 (`DepositController`)

#### `POST /api/terminal/deposit/unlock`
Verifies an `ASSIGNED` parcel at the physical kiosk and commands the compartment door to unlock (`< 3s`, `NFR_03`).
* **Access:** Kiosk Terminal (Parcel ID verification)
* **Request Body:**
```json
{
  "lockerId": "loc-belval-01",
  "parcelId": "p-7a8b9c0d"
}
```
* **Response (`200 OK`):**
```json
{
  "parcelId": "p-7a8b9c0d",
  "compartmentId": "comp-04",
  "compartmentNumber": 4,
  "doorCommand": "UNLOCK"
}
```
* **Errors:** `404 Not Found` (invalid `parcelId`), `409 Conflict` (parcel not `ASSIGNED` to this station)

#### `POST /api/terminal/deposit/confirm`
Called when the compartment door sensor detects closure; transitions parcel to `READY_FOR_PICKUP`, updates compartment to `OCCUPIED`, sets 7-day deadline, generates single-use PIN, and triggers async recipient notification.
* **Access:** Kiosk Terminal
* **Request Body:**
```json
{
  "parcelId": "p-7a8b9c0d",
  "compartmentId": "comp-04",
  "doorClosed": true,
  "parcelDetected": true
}
```
* **Response (`200 OK`):**
```json
{
  "parcelId": "p-7a8b9c0d",
  "status": "READY_FOR_PICKUP",
  "pickupDeadline": "2026-11-26T15:25:00Z",
  "notificationTriggered": true
}
```

---

### 2.5 Guest Recipient Pickup — UC4 (`PickupController`)

#### `POST /api/terminal/pickup/verify`
Validates a guest recipient's 6-digit PIN / QR code at the physical terminal and unlocks the compartment (`NFR_02`, `NFR_03`).
* **Access:** Public Kiosk Terminal (Guest-First MVP)
* **Request Body:**
```json
{
  "lockerId": "loc-belval-01",
  "pickupCode": "482910"
}
```
* **Response (`200 OK`):**
```json
{
  "parcelId": "p-7a8b9c0d",
  "compartmentId": "comp-04",
  "compartmentNumber": 4,
  "doorCommand": "UNLOCK"
}
```
* **Errors:**
  * `401 Unauthorized` — Invalid or expired PIN (increments `failed_attempts`).
  * `423 Locked` — Terminal locked for 15 minutes after 5 consecutive failed attempts (`NFR_02`).

#### `POST /api/terminal/pickup/confirm`
Finalizes collection once the recipient closes the compartment door; marks parcel `COLLECTED`, invalidates the pickup code, and frees the compartment (`AVAILABLE`).
* **Access:** Public Kiosk Terminal
* **Request Body:**
```json
{
  "parcelId": "p-7a8b9c0d",
  "compartmentId": "comp-04",
  "doorClosed": true
}
```
* **Response (`200 OK`):**
```json
{
  "parcelId": "p-7a8b9c0d",
  "status": "COLLECTED",
  "compartmentStatus": "AVAILABLE"
}
```

---

### 2.6 Administrator Monitoring & Control — UC5 (`AdminLockerController`)

#### `GET /api/admin/lockers`
Retrieves all locker stations with real-time occupancy statistics and compartment states.
* **Access:** `ADMIN` (`Bearer JWT`)
* **Response (`200 OK`):**
```json
[
  {
    "lockerId": "loc-belval-01",
    "name": "Belval Plaza Station",
    "operationalStatus": "ONLINE",
    "occupancy": {
      "total": 20,
      "available": 12,
      "reserved": 2,
      "occupied": 5,
      "maintenance": 1
    },
    "compartments": [
      { "compartmentId": "comp-01", "number": 1, "size": "SMALL", "status": "AVAILABLE" },
      { "compartmentId": "comp-02", "number": 2, "size": "MEDIUM", "status": "MAINTENANCE" }
    ]
  }
]
```

#### `PATCH /api/admin/compartments/{compartmentId}/status`
Toggles a compartment between `AVAILABLE` and `MAINTENANCE` (blocking or restoring future assignments).
* **Access:** `ADMIN` (`Bearer JWT`)
* **Request Body:**
```json
{
  "status": "MAINTENANCE"
}
```
* **Response (`200 OK`):**
```json
{
  "compartmentId": "comp-02",
  "status": "MAINTENANCE"
}
```
* **Errors:** `409 Conflict` (cannot set an `OCCUPIED` compartment directly to `AVAILABLE` without parcel clearance)

#### `PATCH /api/admin/lockers/{lockerId}`
Changes the operational status of a whole locker station (`FR_10`). New assignments are only possible while it is `ONLINE`; the statuses of its compartments are not modified.
* **Access:** `ADMIN` (`Bearer JWT`)
* **Request Body:** (`operationalStatus`: `ONLINE`, `OFFLINE` or `MAINTENANCE`)
```json
{
  "operationalStatus": "OFFLINE"
}
```
* **Response (`200 OK`):**
```json
{
  "lockerId": "loc-belval-01",
  "operationalStatus": "OFFLINE"
}
```
* **Errors:** `400 Bad Request` (invalid status), `404 Not Found` (unknown locker)

---

## 3. Standard HTTP Error Envelope
All endpoints return errors in a uniform JSON structure:
```json
{
  "timestamp": "2026-11-19T15:22:00Z",
  "status": 409,
  "error": "CONFLICT",
  "message": "Compartment comp-04 was just reserved by another courier."
}
```