# Modular Design

## Use case 1:  Register a Parcel (Courier)

**Precondition:** be logged in and have a valid JWT.

### Frontend (`CourierDashboard`)
The courier arrives at their dashboard upon successful authentication. The dashboard provides a visual overview of existing registered parcels, packages awaiting compartment assignment, and upcoming deliveries.

From the dashboard, the courier opens the **Parcel Registration Form** to input parcel details into the system:
- **Barcode / External ID** — from the barcode or the external service that is sending the parcel; this is shared with the user for tracking purposes
- **Size of Package** — `SMALL`, `MEDIUM`, `LARGE`.
- **Preferred Destination Locker (`preferredLockerId`)** — the locker station selected by the recipient at checkout.
- **Recipient Contact** — email or phone number for pickup code dispatch upon deposit.
- **Expected Delivery Date & Time**
- **Any extra notes** — ex : Optional instructions (e.g., "Fragile", "Handle with care").


The courier is also informed that the parcel has been successfully or unsuccessfully registered with feedback on what went wrong in the latter case.

### Backend (on POST)

#### 1. Controller Layer (`RegistrationController`)
- Accepts the incoming HTTP POST request containing the courier's form payload.
- Delegates the initilization to the `RegistrationService`.

#### 2. Service Layer (`RegistrationService`)
Enforces validation, data manipulation and domain constraints rules : 
1. Sanitization
2. Format and Constrains Validation : required fields, valid IDs and format, dates 
3. Check for duplicates : using tracking IDs
4. Create Parcel Entity:
   - Generates **parcel ID**, a secure, unique identifier within the system (for assignment, delivery at the locker etc.) from a hash of the barcode / external ID
   - Sets the barcode / internal ID as the **tracking number**
   - Stores the recipient's `preferredLockerId` and contact details.
   - Initializes the **status** of the parcel to `REGISTERED`
   - Sets the parcel's pickup **deadline** using the esstimated delivery date  
   - Records the time and date
5. Send the `Parcel` object to the data repository where it will stored.
6. Return a payload to the controller with SUCCESS status and parcelID, or throw error if validation fails


#### 3. Data Access Layer (`ParcelRepository`)
1. Receives the initialized `Parcel` entity from `RegistrationService`.
2. Saves the record directly into the `Parcels` database table/collection.
- **On Success:** Returns the confirmed stored entity record back to the service layer.
- **On Error:** Returns a error response, which the service layer catches to generate readable feedback for the UI.


## Use Case 2: Assign a Compartment (Courier)

**Precondition:** Courier is logged in (`JWT`), parcel status is `REGISTERED`, and target locker station has available compartments.

### Frontend (`CourierDashboard`)
From the dashboard's Packages Awaiting Assignment list, the courier selects a registered parcel :
- The UI automatically pre-selects the recipient's **preferred destination locker (`preferredLockerId`)**, displays its available compartments grouped by size (`SMALL`, `MEDIUM`, `LARGE`), and highlights the **system's recommended compartment** (smallest available fit).
- If the preferred locker station is full or under maintenance, the courier can select an alternative nearby locker station from a dropdown fallback.
- The courier confirms the suggested compartment (or selects another fitting one) and receives immediate feedback if the assignment succeeded or if the compartment was just taken.

### Backend (on POST / PATCH)

#### 1. Controller Layer (`AssignmentController`)
- Accepts the incoming HTTP request containing `parcelId`, `lockerId` (by default `preferredLockerId`), and `compartmentId` (or auto-assign flag).
- Verifies the courier's JWT and `COURIER` role, then delegates to `AssignmentService`.

#### 2. Service Layer (`AssignmentService`)
Enforces concurrency, matching, and reservation rules:
1. Validates that the parcel exists and has status `REGISTERED`.
2. Checks real-time availability of the requested compartment (or finds the smallest available compartment matching the parcel's size).
3. **Concurrency Lock:** Atomically reserves the compartment so no other courier can claim it simultaneously.
4. Updates the parcel's `status` to `ASSIGNED` and links `compartmentId`.
5. Returns `SUCCESS` with the assigned compartment number, or an error if the locker/size is unavailable.

#### 3. Data Access Layer (`ParcelRepository` & `LockerRepository`)
1. `LockerRepository` updates the compartment status from `AVAILABLE` to `RESERVED` within a database transaction.
2. `ParcelRepository` updates the parcel's `status` to `ASSIGNED` and saves `compartmentId`.
- **On Success:** Returns the updated parcel and compartment records to the service layer.
- **On Error:** Rolls back the transaction and returns a conflict/storage error to the service layer.


## Use Case 3: Deposit a Parcel at the Locker (Courier)

**Precondition:** Parcel status is `ASSIGNED` to a compartment at the current locker station.

### Frontend (`LockerTerminalUI`)
The courier approaches the physical locker kiosk and selects **"Courier Drop-Off"**:
- **Inputs:** Scans or manually types the **Parcel ID**.
- The terminal displays the assigned compartment number, opens the door, and waits for the courier to place the parcel inside and close the door (or click **"Confirm Door Closed"** in the simulator).

### Backend (on POST)

#### 1. Controller Layer (`DepositController`)
- Accepts the incoming HTTP POST request with `parcelId` and `lockerId` (and later the `doorClosed` confirmation signal).
- Delegates execution to `DepositService`.

#### 2. Service Layer (`DepositService`)
1. Validates that the `parcelId` exists, belongs to this `lockerId`, and has status `ASSIGNED`.
2. Triggers the hardware lock command to open the assigned `compartmentId`.
3. Once the door-closure sensor confirms the parcel is inside and the door is locked:
   - Updates parcel `status` to `READY_FOR_PICKUP`.
   - Sets the **7-day pickup deadline** (`depositTime + 7 days`).
4. **Event Trigger:** Emits a `ParcelDeposited` event to the **Notification Service / Gateway** to send the recipient an SMS/email containing the pickup PIN/QR code, locker address, opening hours, and deadline.
5. Returns `SUCCESS` confirmation to the terminal UI.

#### 3. Data Access Layer (`ParcelRepository`)
1. Updates the `Parcels` record with `status = READY_FOR_PICKUP`, `depositedAt`, and `pickupDeadline`.
- **On Success:** Returns the updated parcel record to the service layer.
- **On Error:** Returns an error response so the terminal can alert the courier.


## Use Case 4: Collect a Parcel (Guest Recipient)

**Precondition:** Parcel status is `READY_FOR_PICKUP`, and the guest recipient has received their single-use pickup PIN/QR code via SMS/email.

### Frontend (`LockerTerminalUI`)
The recipient approaches the locker terminal and selects **"Pick Up Parcel"** (no account or login required):
- **Inputs:** Enters the **6-digit Pickup PIN** or scans the **QR code**.
- The screen displays clear collection instructions, unlocks the compartment, and prompts the recipient to take the parcel and close the door.
- If an invalid code is entered, the UI shows the remaining attempts (locking out for 15 minutes after 5 failed attempts).

### Backend (on POST)

#### 1. Controller Layer (`PickupController`)
- Accepts the incoming HTTP POST request containing `lockerId` and `pickupCode`.
- Delegates verification to `PickupService`.

#### 2. Service Layer (`PickupService`)
1. Checks if the terminal/compartment is currently under a **15-minute brute-force lockout**.
2. Validates the `pickupCode` against active `READY_FOR_PICKUP` parcels at that `lockerId` (verifying it is unused and not expired).
   - **If invalid:** Increments failed attempt counter (triggering a 15-min lockout at 5 attempts) and returns an error.
3. **If valid:** Sends the unlock command to the assigned `compartmentId`.
4. Once door closure is confirmed by the sensor:
   - Invalidates the single-use `pickupCode` (`isUsed = true`).
   - Updates parcel `status` to `COLLECTED` and records `collectedAt`.
   - Marks the compartment as `AVAILABLE` again.
5. Returns `SUCCESS` to the terminal UI.

#### 3. Data Access Layer (`ParcelRepository` & `LockerRepository`)
1. `ParcelRepository` updates the parcel (`status = COLLECTED`, `collectedAt`) and invalidates the pickup code.
2. `LockerRepository` updates the compartment status back to `AVAILABLE`.
- **On Success:** Returns confirmation to the service layer.
- **On Error:** Catches database exceptions and returns a readable error response.


## Use Case 5: Monitor & Manage Locker Availability (Administrator)

**Precondition:** Administrator is logged in and has a valid `JWT` with the `ADMIN` role.

### Frontend (`AdminDashboard`)
Upon logging in, the administrator views an overview of all locker stations, real-time occupancy rates, and a grid of individual compartments (`SMALL`, `MEDIUM`, `LARGE`) color-coded by status (`AVAILABLE`, `OCCUPIED`, `MAINTENANCE`).
- **Action:** The administrator clicks a locker station or specific compartment to toggle its status between `AVAILABLE` and `MAINTENANCE` (e.g., for repairs) and receives confirmation feedback.

### Backend (on GET & PATCH)

#### 1. Controller Layer (`AdminLockerController`)
- Accepts `GET /api/admin/lockers` (to fetch site occupancy) and `PATCH /api/admin/compartments/:id/status` (to update operational status).
- Verifies the `JWT` and `ADMIN` role, then delegates to `LockerManagementService`.

#### 2. Service Layer (`LockerManagementService`)
1. **For Monitoring (`GET`):** Aggregates compartments per locker site and calculates real-time occupancy percentages and free counts per size.
2. **For Status Change (`PATCH`):**
   - Validates the target status (`AVAILABLE` or `MAINTENANCE`).
   - Checks if the compartment currently holds an active parcel (if occupied, prevents marking it `AVAILABLE` without resolving the parcel, or flags a warning if set to `MAINTENANCE`).
   - Updates the compartment status so couriers cannot be assigned to `MAINTENANCE` boxes.
3. Returns the updated station/compartment state or an error message.

#### 3. Data Access Layer (`LockerRepository`)
1. Queries all locker sites and their compartments (`GET`) or updates the `status` field in the `Compartments` table (`PATCH`).
- **On Success:** Returns the updated records to the service layer.
- **On Error:** Returns a database error response for the service layer to handle.