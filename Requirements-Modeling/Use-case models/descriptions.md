# Use Cases Textual Descriptions

## 1. Courier Use Cases

### Use Case: Authentification

| Field | Details |
| :--- | :--- |
| **Use Case Name** | Authentification |
| **Actors** | **Primary:** Courier <br> **Secondary:** System App (API etc) |
| **Preconditions** | • Courier is registered at the delivery company <br> • Courier has an existing account |
| **Main Success Scenario** | 1. Courier opens app <br> 2. Courier enters his login credentials <br> 3. Courier accesses the portal |
| **Extensions** | Flow A: Invalid credentials <br> 2a. Courier didn't enter the correct credentials <br> 3a1. Courier can retry <br> 3a2. Courier can select forgot password  |
| **Postconditions** | Courier can register parcels and view his upcoming deliveries. |

---

### Use Case: Register a parcel

| Field | Details |
| :--- | :--- |
| **Use Case Name** | Register a parcel |
| **Actors** | **Primary:** Courier <br> **Secondary:** System App, (Hardware locker) |
| **Preconditions** | • Courier is authenticated <br> • Parcel has a barcode with its information: content, exact size, delivery location, special instructions etc. |
| **Main Success Scenario** | 1. Courier scans the barcode <br> 2. System registers the information and asks validation <br> 3. Courier validates to register parcel. |
| **Extensions** | / |
| **Postconditions** | Courier can view registered parcels and assign them lockers |

---

### Use Case: Assign a compartment

| Field | Details |
| :--- | :--- |
| **Use Case Name** | Assign a compartment |
| **Actors** | **Primary:** Courier <br> **Secondary:** System App, (Hardware locker) |
| **Preconditions** | • Courier is authenticated <br> • Parcel information is registered in the system <br> • Courier can correctly view the available lockers and compartments at the requested location. |
| **Main Success Scenario** | 1. The system displays the available compartment at requested locker <br> 2. The courier chooses an appropriate one based on size <br> 3. The system registers the choice. |
| **Extensions** | Flow A : No available compartment on the chosen delivery location <br> 1a. System alerts the courier and display a nearby locker with available lockers  |
| **Postconditions** | The compartment should be marked unavailable for other deliveries. The hardware locker should receive the information so the courier can place the parcel in the correct compartment. |

---

### Use Case: Deliver a parcel

| Field | Details |
| :--- | :--- |
| **Use Case Name** | Deliver a parcel |
| **Actors** | **Primary:** Courier <br> **Secondary:** System App, Hardware locker, Administrator, Recipient |
| **Preconditions** | • Courier is authenticated <br> • Parcel is registered in the system <br> • An available locker is assigned <br> • Courier arrives at the correct location during open hours |
| **Main Success Scenario** | 1. Courier successfully finds the location at an open hour <br> 2. Courier scans or input parcel code at the terminal <br> 3. System validates and opens assigned locker <br> 4. Courier places parcel inside locker and closes it <br> 5. System sensor confirm it |
| **Extensions** | **Door fails to open (2a) / to lock (3a):** <br> 1. System detects fault OR courier reports <br> 2. System changes Locker status to unavailable <br> 3. System assigns another free, similar locker for the parcel |
| **Postconditions** | System updates parcel status, which notifies the recipient with a pickup code |

---

## 2. Recipient Use Cases

### Use Case: Authentification

| Field | Details |
| :--- | :--- |
| **Use Case Name** | Authentification |
| **Actors** | **Primary:** Recipient <br> **Secondary:** System App, Email / SMS Gateway |
| **Preconditions** | • Recipient has an active order to be delivered at one of the registered lockers. <br> • Recipient has a valid email address or phone number registered with the parcel. |
| **Main Success Scenario** | 1. Recipient opens the app. <br> 2. Recipient enters their email address or phone number. <br> 3. System generates and sends a temporary verification code via SMS or Email. <br> 4. Recipient enters the received verification code into the application. <br> 5. System validates the code and grants access to the portal. |
| **Extensions** | • (Invalid credentials) |
| **Postconditions** | Recipient accesses their active parcel status, parcel history, and notifications. |

---

### Use Case: Receive Pickup Notification

| Field | Details |
| :--- | :--- |
| **Use Case Name** | Receive Pickup Notification |
| **Actors** | **Primary:** Recipient <br> **Secondary:** System App, Hardware locker, Courier |
| **Preconditions** | • Courier is authenticated <br> • Parcel has a barcode with its information: content, exact size, delivery location, special instructions etc. |
| **Main Success Scenario** | 1. Courier confirms parcel placement at the locker terminal. <br> 2. System updates the parcel status to Ready for Pickup. <br> 3. System generates a unique single-use pickup code. <br> 4. System sends a notification (SMS/Email/Push) containing the pickup code, station location, opening hours, and expiration deadline. <br> 5. Recipient views current tracking status and instructions. |
| **Extensions** | • (Courier forgot to log parcel status) <br> • (Recipient can authenticate to view notification and code) |
| **Postconditions** | Recipient has successfully received a valid pickup code, deadline information, and locker station location details |

---

### Use Case: Pickup parcel

| Field | Details |
| :--- | :--- |
| **Use Case Name** | Pickup parcel |
| **Actors** | **Primary:** Recipient <br> **Secondary:** System App, Hardware locker, Administrator |
| **Preconditions** | • Parcel was placed in the assigned locker by the courier <br> • Parcel status is Ready for Pickup <br> • Recipient arrives at the correct location during open hours <br> • Recipient possesses valid pickup code |
| **Main Success Scenario** | 1. Recipient approaches the terminal and selects the pickup option on the screen. <br> 2. Recipient enters or scan pickup code. <br> 3. System verifies the code and opens the assigned compartment of the hardware locker. <br> 4. Recipient retrieves the parcel from the compartment and closes the door. <br> 5. Recipient confirms parcel collection. <br> 6. System updates parcel status to Collected. |
| **Extensions** | • **Wrong code (2a)** <br> • **Door fails to open (3a) / to lock (4a):** 1. System detects fault OR recipient reports |
| **Postconditions** | System updates delivery status to Completed and the locker is marked as available |
