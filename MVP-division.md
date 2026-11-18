## MVP Work Division

Objective : guarantee a unified user experience across all interfaces while keeping clear, isolated individual module ownership and minimal Git merge conflicts, the MVP implementation is divided as follows:

| Member | Primary Role & Module | Deliverables |
| :--- | :--- | :--- |
| **Vanathy** | **Frontend & UI Coherence Lead** (Presentation Layer) | • Shared UI shell, navigation, styling, and HTTP/JWT client wrapper<br>• `LoginUI`, `CourierDashboard`, `AdminDashboard`, and `LockerTerminalUI` views connected to the backend REST API |
| **Member 2** | **Database, Auth & RBAC Service** | • PostgreSQL schema, migrations, and seed scripts (`Users`, `Lockers`, `Compartments`, `Parcels`)<br>• `AuthController`, `AuthService`, `UserRepository`, JWT login & RBAC middleware (**FR_05**, **NFR_01**) |
| **Member 3** | **Parcel Registration & Assignment Module** (UC1 & UC2) | • `RegistrationController`, `RegistrationService` (**FR_02**, **FR_03**)<br>• `AssignmentController`, `AssignmentService` (**FR_04**, **NFR_04**)<br>• `ParcelRepository` |
| **Member 4** | **Locker Deposit & Event Notification Service** (UC3) | • `DepositController`, `DepositService` (`ASSIGNED` -> `READY_FOR_PICKUP`, **FR_06**)<br>• Notification Service / Gateway (`ParcelDeposited` event handler -> SMS/Email dispatch **FR_07**) |
| **Member 5** | **Guest Collection & Terminal Security Service** (UC4) | • `PickupController`, `PickupService` (**FR_01**, **FR_08**, **NFR_02**, **NFR_03**) |
| **Member 6** | **Admin Locker Monitoring & Management Service** (UC5) | • `AdminLockerController`, `LockerManagementService`, `LockerRepository` (**FR_09**, **FR_10**) |

### Key Integration Rules
1. **Freeze the REST API Contract First:** Agree on exact endpoint URLs and JSON request/response payloads before coding so Member 1 can build the UI against mock JSON immediately while Members 2–6 implement the backend.
2. **Strict Layer Separation:** Keep business rules (validation, compartment sizing, lockout timers) inside Members 2–6's backend services rather than in the frontend.
3. **Incremental Integration:** Connect and test flows one slice at a time (`Login` + `UC1` -> `UC2` -> `UC3/UC4` -> `UC5`) via feature branches and peer-reviewed Pull Requests.

### Technology choice : 

Option 1 : Full stack Typescript :
- Backend & Notification server : Node.js + Express in TS : 
    * Non-blocking I/O handles concurrent terminal polling and event-driven webhook/SMS triggers naturally. 
    * Sharing TypeScript interfaces (Parcel, Compartment, UserRole) between the frontend, core server, and notification worker eliminates API contract mismatches.
    * PostgreSQL Access: Prisma or Drizzle ORM (provides clean repository abstractions, parameterized queries against SQL injection, version-controlled migrations, and straightforward SELECT ... FOR UPDATE transactions for compartment locking).
- Frontend : React + TS (with Vite) : 
    * Component-based UI makes it easy to reuse layout shells, status badges, and JWT Axios/Fetch interceptors across the Courier, Admin, and Locker Terminal views.
- Database : PostgreSQL for relational schemas, foreign keys, indexes and atomic concurrency transactions
- Tests : Jest or Vitest to unit-test Service Layer rules


Option 2 : Python Backend + React TS Frontend :
- Backend & Notification server : Python 3.12+ and FastAPI : 
    * FastAPI natively enforces JSON request/response validation via Pydantic schemas (Controller/Service validation rules), generates automatic interactive Swagger/OpenAPI docs at /docs (making backend / frontend integration seemless), and supports async background tasks for your Notification Gateway.
    * PostgreSQL Access: SQLAlchemy 2.0 (with Alembic for schema migrations and row-level locking).
- Frontend : React + TS (with Vite) : 
    * Component-based UI makes it easy to reuse layout shells, status badges, and JWT Axios/Fetch interceptors across the Courier, Admin, and Locker Terminal views.
- Database : PostgreSQL for relational schemas, foreign keys, indexes and atomic concurrency transactions
- Tests : Pytest to unit-test Service Layer rules