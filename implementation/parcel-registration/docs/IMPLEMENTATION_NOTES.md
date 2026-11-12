# Implementation traceability — Register a Parcel (Courier)

**Source:** [Modular-Design.md](https://github.com/vanubala/SE_Team3_2026/blob/main/Modular-Design.md) (GitHub, `main`, reviewed November 2026). Also see `Requirements-Modeling/Requirements-analysis.md` user stories C0 and C1.

| Team design item | Implementation | Test/evidence |
|---|---|---|
| Courier dashboard after login | `frontend/index.html`, `frontend/app.js` | Browser + `test_api_health_and_frontend` |
| JWT authentication precondition | `app/auth.py`, required in `controller.py` | missing/invalid/expired/role tests |
| Barcode/external ID | `models.py` `barcode`, persisted as tracking number | success and invalid barcode tests |
| Size enum SMALL/MEDIUM/LARGE | `ParcelSize` | success and invalid size tests |
| Expected delivery datetime | timezone-aware validator | future and naive datetime tests |
| Extra notes | sanitized, length limited, plain-text DOM | notes sanitation test |
| Success/failure UI | `frontend/app.js` feedback panel | API test status/response |
| Controller delegates to service | `app/controller.py` | API tests exercise delegation |
| Sanitize & validate | `models.py` | validation tests |
| Check duplicate tracking ID | `service.py` and DB `UNIQUE` | duplicate test |
| Generate parcel ID from hash | keyed HMAC-SHA256 using barcode | deterministic / keyed hash test |
| Set tracking number | `tracking_number=barcode` | success test |
| Set status REGISTERED | `service.py` | success test |
| Pickup deadline from expected date | +72 hours assumed, configurable | success test |
| Creation timestamp | server's UTC time | success response test |
| Save Parcel in repository | `app/repository.py` via SQLite | persistence test |
| Repository error propagation | unique constraint maps to 409; other errors propagate to 500 | duplicate tests; normal exception flow |

## What this does not claim to implement

- C0 login/password reset/QR/PIN authentication; it only verifies a JWT that another component would issue.
- Compartment assignment, locker hardware, actual delivery, pickup notifications, recipient management, or account registration.
- Full production-ready availability/security/compliance; this is one use-case implementation with an explicitly local development mode.

## Recommended next steps in team meeting

1. Review expected pickup-deadline rule and barcode format.
2. Set shared API and authentication contracts.
3. Choose one stack before integrating; decide ownership of the auth module.
4. Include test evidence and a short demonstration in the deliverable; credit the developer who implements/validates the module.
