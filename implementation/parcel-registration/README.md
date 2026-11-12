# Smart Parcel Locker — Register a Parcel (Courier)

**Standalone, working implementation of use case C1**, based on the team's [`Modular-Design.md`](https://github.com/vanubala/SE_Team3_2026/blob/main/Modular-Design.md) and requirements (`FR_03`, `FR_05`, `C0`, `C1`). It is included as an isolated prototype, **not yet integrated into the team's main application**. The team has not yet selected an application stack; this is a demonstrable reference implementation.

## Quick start (Windows / macOS / Linux)

Requires **Python 3.11+**.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python run_demo.py
```

Open **http://127.0.0.1:8000**, click **Start local demo session**, and register a test parcel. Data is stored locally in `data/demo-parcels.sqlite3`. The demo runner generates new random JWT/parcel-ID secrets on each start and binds to **localhost only**. It is **not a production authentication system**.

### Run automated tests

```bash
python -m pytest -q
```

### Production-style mode (integrate your real authentication)

Set strong independent secrets and other settings using `.env.example` as a reference (do **not** commit actual secrets). This project deliberately does **not** implement the team's C0 login flow, but verifies its signed courier JWT:

```bash
# Set JWT_SECRET, PARCEL_ID_SECRET, DATABASE_PATH, etc. in your environment.
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

By default, this mode has **no token-generation endpoint**. Tokens must come from the external authentication module. A courier JWT must have `sub`, `role=COURIER`, `iss`, `aud`, `exp` claims and a valid HS256 signature. Match the issuer/audience/secret to your actual auth module. The security rules can also be switched to an external public-key verification system during integration.

## Architecture

```text
Browser: CourierDashboard (frontend/index.html + app.js + styles.css)
    POST /api/parcels  (Authorization: Bearer <signed courier JWT>)
        |
    app/auth.py  --> requires valid JWT and COURIER role
        |
    app/controller.py : RegistrationController (HTTP, response/error mapping)
        |
    app/service.py    : RegistrationService (business rules, IDs, deadline)
        |
    app/repository.py : ParcelRepository (parameterised SQLite SQL + UNIQUE tracking number)
        |
    data/parcels.sqlite3 (local Parcels table)
```

## API contract

`POST /api/parcels` requires a signed bearer token with role `COURIER`.

```json
{
  "barcode": "TRACK-2026-0042",
  "size": "MEDIUM",
  "expectedDeliveryAt": "2026-12-12T14:00:00+01:00",
  "notes": "Fragile, handle with care"
}
```

`201 Created`:

```json
{
  "status": "SUCCESS",
  "parcelId": "<64-character server-derived HMAC-SHA256 identifier>",
  "parcel": {
    "parcelId": "<same ID>",
    "trackingNumber": "TRACK-2026-0042",
    "size": "MEDIUM",
    "expectedDeliveryAt": "2026-12-12T13:00:00Z",
    "notes": "Fragile, handle with care",
    "status": "REGISTERED",
    "pickupDeadline": "2026-12-15T13:00:00Z",
    "createdAt": "<server UTC timestamp>"
  }
}
```

Also provides `GET /api/parcels` (the current courier's latest 50 registrations), `/health`, and a local-only demo token endpoint when run via `run_demo.py`.

| Condition | Status | Behaviour |
|---|---:|---|
| New valid registration | 201 | Returns `SUCCESS` and parcel ID |
| Missing, invalid or expired JWT | 401 | Reject |
| Authenticated user without `COURIER` role | 403 | Reject |
| Duplicate barcode | 409 | Does not overwrite earlier parcel |
| Invalid size/barcode/datetime/notes | 422 | Input errors returned to form |
| Unexpected repository failure | 500 | No false `SUCCESS` response |

The frontend escapes all user-supplied values by inserting them as DOM text, rather than inserting unsafe HTML.

## Documented assumptions / questions for the team

1. **Hash-derived parcel ID:** plain `SHA256(barcode)` is easy to predict if barcodes are known. This prototype follows the requirement *in spirit* but uses `HMAC-SHA256(barcode, secret)` to generate a deterministic opaque 64-character ID. A random UUID would also be appropriate if the team revises the specification. ID and barcode are separate fields.
2. **Pickup deadline:** `Modular-Design.md` says to calculate this from the *expected delivery date* but gives no pickup window. This prototype **assumes 72 hours after expected delivery**, configurable via `PICKUP_WINDOW_HOURS`. In a real locker system the deadline would normally be set when the parcel is actually deposited and made available for pickup; **confirm this with the team before production**.
3. **Barcode format:** the prototype allows 3–64 ASCII letters, digits, hyphens or underscores. External logistics partners may use different barcode formats. Confirm the actual upstream format.
4. **Courier identity:** this module accepts the identity/role in a correctly signed JWT; it does not issue real courier credentials or register courier accounts. Integration with the team's authentication (C0) is necessary.
5. **No compartment assignment or deposit:** those are separate use cases; `REGISTERED` is the only initial status. Dashboard "Awaiting assignment" represents parcels still in that status. An upcoming-delivery count is based on expected dates for the **50 most recent** parcels (not an all-time global aggregate).
6. **Privacy/production hardening:** no personally identifying recipient data is required by this use case. For deployment, add HTTPS, operational monitoring, CSRF/cookie handling if auth model changes, standard CORS policy, secret management, shared DB migrations, and failure telemetry.

## Suggested team integration

- Decide the common frontend/backend stack first. The implementation uses FastAPI + SQLite only because the GitHub repository has no application code yet.
- Keep this as an isolated proof-of-concept or port its controller/service/repository logic to the agreed stack.
- Use the API contract and tests as acceptance criteria for Deliverable 2.
- Review assumptions 1–4 before merging any implementation into the shared system.

## File map

- `app/auth.py` — JWT signature/claims verification (separate from C0 login)
- `app/controller.py` — HTTP endpoints (`RegistrationController`)
- `app/models.py` — request/response validation
- `app/service.py` — `RegistrationService`
- `app/repository.py` — `ParcelRepository`, SQLite `Parcels` collection
- `frontend/` — live courier dashboard and registration form
- `tests/` — tests for registration, permissions, duplicates, dates, persistence and errors
- `docs/IMPLEMENTATION_NOTES.md` — mapping of teammates' design to code
