# Smart Parcel Locker — Deposit and Notification (UC3)

The UC3 `DepositController`, `DepositService`, repository adapter, pickup-PIN issuer, and notification gateway. It follows the team's `Modular-Design.md`, `Schemas-Endpoints.md`, and feature-branch / peer-review workflow. The shared database/auth backend from PR #39 is on `main` under `src/backend`; UC2 assignment (PR #40) and UC5 locker management (PR #38) are still separate feature branches.

## Run the local demo

Requires Python 3.12+.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python run_demo.py
```

Open `http://127.0.0.1:8000/docs`. The runner prints a demo locker ID, compartment ID, and assigned parcel ID. Set the `X-Demo-Locker-ID` header to the printed locker ID for both endpoints. By default the demo binds to localhost, uses a local SQLite database, logs a simulated door command, and uses the redacted console notification stand-in.

## Automated checks

From this directory, install the development dependencies and run the UC3 tests:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The tests use the local SQLite models and fake notification/hardware adapters. They cover PIN generation and verification, authorization and sensor validation, deposit commit and retry behavior, idempotent confirmation, notification contents/retries, the `RESERVED -> OCCUPIED` transition, and the maintenance-after-unlock decision. No shared team service, provider credentials, or physical locker is required.

To send real messages, create Twilio Programmable Messaging and Twilio SendGrid credentials, copy `.env.example` to `.env`, set `PICKUP_NOTIFICATION_PROVIDER=twilio-sendgrid`, then fill in the Twilio account/API key and sender number or Messaging Service SID, plus the SendGrid API key and verified sender email. The Twilio adapter sends phone contacts as SMS; the SendGrid adapter sends email contacts. Do not commit `.env`. `PICKUP_CODE_SECRET` must be a random secret of at least 32 bytes and match the secret UC4 uses. If it is omitted, the local demo generates an in-memory secret for that run.

## Endpoints

| Method and path | Purpose |
|---|---|
| `POST /api/terminal/deposit/unlock` | Verify assignment and locker state, then command the assigned door to unlock |
| `POST /api/terminal/deposit/confirm` | Confirm door closure and parcel detection, persist the deposit and pickup code, then schedule notification |

Unlock request:

```json
{"lockerId":"<locker-id>","parcelId":"<parcel-id>"}
```

Unlock response:

```json
{"parcelId":"...","compartmentId":"...","compartmentNumber":4,"doorCommand":"UNLOCK"}
```

Confirmation request:

```json
{"parcelId":"...","compartmentId":"...","doorClosed":true,"parcelDetected":true}
```

Confirmation response:

```json
{"parcelId":"...","status":"READY_FOR_PICKUP","pickupDeadline":"...","notificationTriggered":true}
```

## Deposit rules

- A new unlock is refused unless the parcel is `ASSIGNED` to a `RESERVED` compartment at the terminal's locker and the locker is `ONLINE`. A compartment already in `MAINTENANCE` is never opened for a new deposit.
- The door gateway is called only after those checks succeed. A hardware failure returns `503`.
- Confirmation requires both `doorClosed` and `parcelDetected` to be true.
- A successful confirmation sets the parcel to `READY_FOR_PICKUP`, records `deposited_at`, sets the deadline to seven days after deposit, and stores a single-use pickup-code hash. PIN collisions are rejected by a unique `code_hash` constraint and retried with a newly generated PIN.
- Raed's `LockerRepository.occupy_compartment()` owns the `RESERVED -> OCCUPIED` transition and version increment. If an administrator changes the compartment to `MAINTENANCE` after the door was unlocked but before confirmation, and sensors confirm the parcel is physically inside, UC3 records the parcel and pickup code while preserving `MAINTENANCE`. It does not call `occupy_compartment()` for that state, since UC5 correctly rejects it. This avoids losing track of a parcel that is already in the locker.
- A repeated confirmation does not create another code or send another notification.
- The notification is scheduled only after the database transaction commits.

## Integration

The shared backend on `main` defines the `Locker`, `Compartment`, `Parcel`, and `PickupCode` fields this adapter needs. Pass those classes from `src/backend/app/db/models.py` and the request-scoped SQLAlchemy `Session` provided by `app.db.session.get_db`. PR #40 leaves assignments as parcel `ASSIGNED` and compartment `RESERVED`, which is the state UC3 expects. Use the unified `LockerRepository` from the UC5/UC2 work with the same session so parcel, compartment, and pickup-code writes commit or roll back together.

At app assembly, inject:

1. Shared `Parcel`, `Compartment`, `Locker`, and `PickupCode` ORM classes into `SQLAlchemyDepositRepository`.
2. The unified UC5/UC2 `LockerRepository` instance for that same session. UC3 uses `get_compartment_for_update()` and `occupy_compartment()` from PR #38; UC2's `reserve_compartment()` is used before UC3 receives the parcel.
3. `require_locker_terminal`, which maps an authenticated physical kiosk to its authorized locker. Do not trust a caller-supplied locker ID as terminal identity.
4. A `CompartmentDoorGateway` implementation for actual hardware. `ConsoleDoorGateway` simulates the command, so no physical locker is needed to finish and review the UC3 service code. Replace it when the device/API is available; physical hardware testing is a later deployment check.
5. A `PickupCodeIssuer` secret shared with UC4. `hash_code()` and `verify()` use HMAC-SHA256 over the six-digit ASCII PIN; store only the hash.
6. `TwilioSendGridGateway` sends phone contacts through Twilio and email contacts through SendGrid. `ConsolePickupGateway` remains the safe default for the local demo; select the real adapter with `PICKUP_NOTIFICATION_PROVIDER=twilio-sendgrid` and environment credentials.

Include `DepositController(...).router` in the shared FastAPI app and register the standard HTTP error-envelope handlers once at app level. Repository methods do not commit; `DepositService` owns commit/rollback.

The shared `PickupCode` model on `main` has the required fields `code_id`, `parcel_id`, `code_hash`, `failed_attempts`, `locked_until`, `issued_at`, `expires_at`, and `used_at`. This contribution adds a database migration at `src/backend/migrations/versions/0002_unique_pickup_code_hash.py`, enforcing unique stored hashes so concurrent deposits cannot issue the same six-digit PIN. It does not edit the existing shared model file or any teammate-owned implementation. The UC3 adapter initializes failed attempts to zero and the lock/use timestamps to null. See `integration/PICKUP_CODE_SCHEMA_FIX.md` for rollout notes.

The new `.github/workflows/uc3-deposit-notification.yml` runs the UC3 tests and validates the shared Alembic migration chain. It is separate from the existing authentication workflow and leaves that workflow unchanged.

The current API schema and PR #40 both leave pickup-code creation to deposit, so UC3 generates the PIN when the parcel becomes `READY_FOR_PICKUP`. The broader requirements notes should be kept aligned with that timing.

## Package layout

- `deposit_notification/controller.py` — FastAPI routes and error mapping.
- `deposit_notification/demo.py` and `run_demo.py` — localhost-only SQLite demo with replaceable stand-in models and locker repository.
- `deposit_notification/demo_models.py` — demo ORM classes; replace with the team's shared model classes during integration.
- `deposit_notification/service.py` — UC3 business rules and transaction boundary.
- `deposit_notification/repository.py` — SQLAlchemy adapter that reuses UC5 compartment locking and transitions.
- `deposit_notification/security.py` — six-digit PIN generation, HMAC-SHA256 hashing, and verification helper for UC4.
- `deposit_notification/hardware.py` — console door-command stand-in.
- `deposit_notification/notifications.py` — async notification handler and console gateway stand-in.
- `deposit_notification/providers.py` — asynchronous Twilio SMS and SendGrid email provider adapter.
- `deposit_notification/errors.py` — standard error envelope for the local demo only.
- `deposit_notification/contracts.py` — API DTOs, terminal identity, domain events, and adapter protocols.

This contribution adds the UC3 module, one new database migration, and one new UC3 workflow. It does not modify existing team implementation files.
