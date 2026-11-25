# Requirements analysis

## Stakeholders

* **Primary:** Courier (Requirement provider, validator), Recipient (Requirement provider, validator), Administrator (Requirement provider, decision-maker, validator)
* **Secondary:** Host businesses (Requirement provider, constraint source)
* **External:** EU regulations / GDPR (Constraint source, requirement provider)
* **Hidden:** IT operations and development team (Maintainer/operator), Locker hardware & maintenance team (Domain expert, constraint source)


## Activities & Tasks

| Activity | Tasks | Linked Requirements |
|---|---|---|
| **Deliver a parcel (Courier)** | Log in to dashboard; register parcel; assign compartment; deposit via Parcel ID; report exceptions & retrieve expired parcels | FR_02, FR_03, FR_04, FR_05, FR_06, FR_07, FR_13, FR_14, NFR_01, NFR_03, NFR_04 |
| **Collect a parcel (Recipient)** | Receive pickup code; unlock & collect parcel at terminal; track parcel & recover code; report issues & extend deadline | FR_01, FR_02, FR_07, FR_08, FR_11, FR_12, FR_13, FR_18, NFR_02, NFR_03, NFR_08, NFR_10 |
| **Manage & monitor system (Administrator)** | Log in to admin portal; visualise locker availabilities; change locker status; handle issues & expired pickups; monitor telemetry & audit logs | FR_05, FR_09, FR_10, FR_13, FR_14, FR_15, FR_16, FR_17, NFR_01, NFR_05, NFR_06, NFR_07, NFR_09 |


## Conflicts

| Conflict | Perspective 1 | Perspective 2 |
|---|---|---|
| **Pickup deadline** | Recipients: long deadlines and extensions. | Management and couriers: compartments freed quickly to keep capacity for new parcels. |
| **Privacy vs investigation** | Administrators: full recipient details and long history to investigate issues. | EU (GDPR): data minimisation and short retention. |
| **Opening hours** | Recipients: 24/7 access to their parcel. | Host businesses: access only during their opening hours, no disturbance. |
| **Cost vs quality** | Management: low development and operating cost. | Recipients and IT team: reliable alerts, offline validation, fast response times. |


## Requirements

### Functional Requirements

| ID | Requirement | Release | Linked Stories |
|---|---|---|---|
| **FR_01** | **Guest Collection:** Recipients do not need an account to collect parcels; they receive a single-use pickup PIN/QR code via SMS/email and use it directly at the terminal. | **MVP** | R2, R4 |
| **FR_02** | **Parcel Lifecycle:** The system tracks parcel statuses: `REGISTERED` → `ASSIGNED` → `READY_FOR_PICKUP` → `COLLECTED`. | **MVP** | C1, C3, C5, R5 |
| **FR_03** | **Parcel Registration:** Authenticated couriers can register an incoming parcel by submitting its external ID, size (`SMALL`, `MEDIUM`, `LARGE`), expected delivery date/time, and optional notes; the system validates uniqueness, generates a hashed internal Parcel ID, sets the pickup deadline (7 days from deposit), and saves it as `REGISTERED`. | **MVP** | C0, C1 |
| **FR_04** | **Compartment Assignment:** For a `REGISTERED` parcel, the courier can view locker locations, opening hours, and free compartments per size, and assign/reserve the smallest available compartment matching the parcel size (`ASSIGNED`), generating a secret pickup code (not yet sent) and preventing double-booking. | **MVP** | C2, C3, C6 |
| **FR_05** | **Authentication & Roles:** Couriers and Administrators authenticate on the web portal (JWT) with Role-Based Access Control (`Courier`, `Administrator`) enforcing endpoint permissions. | **MVP** | C0, A0 |
| **FR_06** | **Deposit at Locker:** At the locker terminal, the courier scans or enters the `ASSIGNED` parcel's ID to unlock the pre-assigned compartment; hardware sensors verify parcel placement and door closure before updating status to `READY_FOR_PICKUP`. | **MVP** | C4, C5 |
| **FR_07** | **Pickup Notification Dispatch:** Upon deposit confirmation (`READY_FOR_PICKUP`), the system dispatches an SMS/email notification to the recipient containing the single-use pickup PIN/QR code, locker address, opening hours, pickup deadline, and instructions. | **MVP** | C5, R2, R3 |
| **FR_08** | **Parcel Collection:** At the locker terminal, the guest recipient enters their pickup PIN or scans their QR code to unlock the assigned compartment; hardware sensors verify door closure to mark the parcel `COLLECTED` and release the compartment. | **MVP** | R4, R5 |
| **FR_09** | **Locker Occupancy Visualisation:** Administrators can visualise real-time compartment availability and occupancy per site. | **MVP** | A1, A9 |
| **FR_10** | **Manual Locker Status Update:** Administrators can manually change a locker or compartment status (`Available`, `Unavailable`, `Maintenance`) to block new assignments during faults or repairs, and restore it to service afterward. | **MVP** | A3, A4 |
| **FR_11** | **Recipient Account & Live Tracking:** Recipients can register/log in with email or phone (OTP) to track active parcels and view statuses (`REGISTERED`, `ASSIGNED`, `READY_FOR_PICKUP`, `DELAYED`, `LOCKER_UNAVAILABLE`, `PICKUP_EXPIRED`, `RETURNED`). | **Release 1** | R0, R1 |
| **FR_12** | **Pickup Code Recovery & Reminders:** Recipients can request a re-send of an active pickup code if lost, and the system automatically sends expiry reminders (e.g., 24h and 4h before the 7-day deadline). | **Release 1** | R2, R6 |
| **FR_13** | **On-Site Issue Reporting:** Couriers and recipients can report on-site issues (door jammed, parcel damaged, size mismatch, empty compartment) with structured fault categories, receive immediate instructions, and allow admins to track and resolve reported issues. | **Release 1** | C7, C8, R8, R9, A5, A6 |
| **FR_14** | **Expiry Handling & Courier Retrieval:** When the 7-day pickup window ends, the parcel is automatically marked `PICKUP_EXPIRED` and added to the courier's collection list so the compartment can be cleared and freed. | **Release 1** | C9, R7, A10 |
| **FR_15** | **Automated Hardware Telemetry:** The system receives automated operational telemetry from hardware lockers (door sensor faults, offline heartbeats, power anomalies) and alerts administrators. | **Release N** | A2 |
| **FR_16** | **Maintenance Team Escalation:** When a hardware fault is detected or reported, administrators can escalate and dispatch a fault ticket to the external Maintenance Team. | **Release N** | A6, A11 |
| **FR_17** | **Audit & History Logs:** Authenticated recipients and administrators can view full historical event logs for parcels and locker maintenance. | **Release N** | R10, A7, A8 |
| **FR_18** | **Deadline Extension & GDPR Erasure:** Recipients can request a one-time extension to their pickup deadline before expiration, and users can delete their account/personal data (GDPR right to erasure). | **Release N** | R11, R12 |


### Non-Functional Requirements

| ID | Category | Requirement | Release |
|---|---|---|---|
| **NFR_01** | **Security (Portal Auth)** | All courier and administrator portal login endpoints and protected API routes must be secured over HTTPS using token-based authentication (JWT). | **MVP** |
| **NFR_02** | **Security (Pickup Codes)** | Pickup codes must be random, unique, and single-use, becoming invalid immediately after collection or expiry. Terminal PIN entry locks for 15 minutes after 5 failed attempts. | **MVP** |
| **NFR_03** | **Performance (Hardware)** | A compartment door unlock command must execute in `< 3 seconds` after a valid pickup code or assigned Parcel ID is submitted at the terminal. | **MVP** |
| **NFR_04** | **Reliability (Concurrency)** | Compartment reservation and parcel status transition endpoints must enforce atomic concurrency control (optimistic/pessimistic locking) so simultaneous requests never double-book a compartment or lose state events. | **MVP** |
| **NFR_05** | **Performance (Web/API)** | Portal page loads and compartment availability queries must respond in `< 2 seconds` for 95% of requests under normal load. | **Release 1** |
| **NFR_06** | **Reliability (Availability)** | The core backend API and locker terminal services must maintain $\ge 99.5\%$ uptime during operational hours. | **Release 1** |
| **NFR_07** | **Reliability (Fault Isolation)** | Hardware or network failures at a single locker station or compartment must be isolated, automatically flagging affected parcels as `LOCKER_UNAVAILABLE` without degrading operations at other stations or compartments. | **Release 1** |
| **NFR_08** | **Reliability (Offline Mode)** | Locker terminals cache active pickup codes locally so valid guest recipients can still unlock compartments during temporary network outages, syncing logs once reconnected. | **Release N** |
| **NFR_09** | **Security (Auditability)** | All critical state-changing actions (login attempts, compartment assignments, door unlocks, manual overrides) must be recorded in an immutable audit log with actor ID, timestamp, and target entity. | **Release N** |
| **NFR_10** | **Privacy (GDPR)** | Upon account deletion request, personal user data must be permanently removed or anonymized within 24 hours. | **Release N** |


## User Stories

### Courier User Stories

| ID | Title | User Story | Release | Linked FRs |
|---|---|---|---|---|
| **C0** | Authenticate Courier (Portal) | As a courier, I want to log into the courier web dashboard using my delivery company account, so that I can register parcels and manage assignments. | **MVP** | FR_03, FR_05 |
| **C1** | Register a Parcel | As a courier, I want to register an incoming parcel in the dashboard (barcode, size, expected delivery, notes), so that it is recorded and prepared for assignment. | **MVP** | FR_02, FR_03 |
| **C2** | View Available Lockers | As a courier, I want to see available lockers and free compartment sizes, so that I can find space for a registered parcel. | **MVP** | FR_04 |
| **C3** | View Locker Information | As a courier, I want to see the location and opening hours of the target locker, so that I can plan my delivery efficiently. | **MVP** | FR_02, FR_04 |
| **C4** | Scan Parcel ID to Deposit | As a courier, I want the pre-assigned compartment to open directly when I scan or enter the Parcel ID at the terminal, so that I can deposit the parcel quickly without logging in at the kiosk. | **MVP** | FR_06 |
| **C5** | Confirm Parcel Placement | As a courier, I want the system to verify door closure and confirm placement, so that the parcel status updates to `READY_FOR_PICKUP` and the recipient is notified. | **MVP** | FR_02, FR_06, FR_07 |
| **C6** | Receive Compartment Suggestion | As a courier, I want the system to automatically suggest and reserve the smallest suitable compartment based on parcel size, so that capacity is optimized. | **MVP** | FR_04 |
| **C7** | Report Delivery Exception | As a courier, I want to report an issue during deposit (damaged parcel, size mismatch, jammed door), so that the problem is logged. | **Release 1** | FR_13 |
| **C8** | Receive Support Instructions | As a courier, I want to receive clear instructions after reporting an issue, so that I know how to proceed with the parcel. | **Release 1** | FR_13 |
| **C9** | Collect Expired Parcels | As a courier, I want to view and collect expired parcels from lockers, so that compartments are freed for new deliveries. | **Release 1** | FR_14 |

### Recipient User Stories

| ID | Title | User Story | Release | Linked FRs |
|---|---|---|---|---|
| **R2** | Receive / Recover Pickup Code | As a guest recipient, I want to receive (and re-request in Release 1) a unique pickup PIN/QR code and deadline via SMS/email upon deposit, so that I can collect my parcel without creating an account. | **MVP** / **R1** | FR_01, FR_07, FR_12 |
| **R3** | View Locker Information | As a guest recipient, I want to receive the locker's address, GPS location, and opening hours in my pickup message, so that I can access it easily. | **MVP** | FR_07 |
| **R4** | Enter Code to Open Locker | As a guest recipient, I want the compartment to open when I enter my PIN or scan my QR code at the terminal, so that I can retrieve my parcel. | **MVP** | FR_01, FR_08 |
| **R5** | Confirm Collection | As a guest recipient, I want the system to record my collection once I close the compartment door, so that the delivery is completed. | **MVP** | FR_02, FR_08 |
| **R0** | Authenticate Recipient | As a recipient, I want to log into a web portal using my email or phone number, so that I can view my active parcels. | **Release 1** | FR_11 |
| **R1** | Track Parcel Status | As a recipient, I want to track the live status of my parcel (in transit, delayed, ready, expired), so that I know where my order is. | **Release 1** | FR_11 |
| **R6** | Receive Pickup Reminder | As a recipient, I want to receive automated reminders before my 7-day pickup deadline expires, so that I do not forget my parcel. | **Release 1** | FR_12 |
| **R7** | View Expiry Rules | As a recipient, I want to see what happens if my pickup window expires, so that I understand return procedures. | **Release 1** | FR_11, FR_14 |
| **R8** | Report Pickup Issue | As a recipient, I want to report a problem at the locker (door jammed, code unreadable, empty compartment), so that I can get support. | **Release 1** | FR_13 |
| **R9** | Receive Support Instructions | As a recipient, I want to receive clear guidance after reporting an issue, so that my problem gets resolved. | **Release 1** | FR_13 |
| **R10** | View Parcel History | As a recipient, I want to view my past deliveries and collection logs, so that I can keep track of my orders. | **Release N** | FR_17 |
| **R11** | Extend Pickup Time | As a recipient, I want to request a one-time extension to my pickup deadline, so that I have more time to collect my parcel. | **Release N** | FR_18 |
| **R12** | Delete Recipient Account | As a recipient, I want to delete my account and personal data from the platform, so that my privacy is respected under GDPR. | **Release N** | FR_18 |

### Administrator User Stories

| ID | Title | User Story | Release | Linked FRs |
|---|---|---|---|---|
| **A0** | Authenticate Administrator | As an administrator, I want to log in securely to the admin portal, so that only authorized staff can manage the locker network. | **MVP** | FR_05 |
| **A1** | Visualise Locker Availabilities | As an administrator, I want to visualise locker availability across sites, so that I can see which compartments are available, occupied, or full. | **MVP** | FR_09 |
| **A3** | Mark Locker Unavailable | As an administrator, I want to mark a locker or compartment as unavailable/maintenance, so that couriers cannot assign parcels to it. | **MVP** | FR_10 |
| **A4** | Restore Locker to Service | As an administrator, I want to mark a repaired locker as operational again, so that it becomes available for deliveries. | **MVP** | FR_10 |
| **A9** | Monitor Site Occupancy | As an administrator, I want to see compartment occupancy counts per location, so that I can monitor network capacity. | **MVP** | FR_09 |
| **A5** | View Support Requests | As an administrator, I want to view support reports submitted by couriers and recipients, so that I can respond to issues. | **Release 1** | FR_13 |
| **A6** | Manage Locker Issues | As an administrator, I want to update the status of reported locker issues, so that problems are tracked until resolved. | **Release 1** | FR_13, FR_16 |
| **A10** | View Expired Pickups | As an administrator, I want to view parcels that have passed their pickup deadline, so that courier collection can be tracked. | **Release 1** | FR_14 |
| **A2** | Receive Operational Status | As an administrator, I want to receive real-time operational status and telemetry alerts from lockers, so that I can identify broken or offline stations. | **Release N** | FR_15 |
| **A7** | View Parcel History | As an administrator, I want to view the full event history of a parcel, so that I can investigate disputes or lost items. | **Release N** | FR_17 |
| **A8** | View Locker History | As an administrator, I want to view the usage and maintenance history of a locker, so that I can spot recurring faults. | **Release N** | FR_17 |
| **A11** | Report to Maintenance Team | As an administrator, I want to escalate confirmed hardware faults to the external Maintenance Team, so that physical repairs are dispatched. | **Release N** | FR_16 |