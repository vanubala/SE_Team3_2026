# Backend integration notes

- **Authentication:** `POST /api/auth/login` verifies staff passwords with Argon2id and issues a signed JWT. Tokens default to 30 minutes. Use `require_courier`, `require_admin`, or `current_user` on staff routes. Guest pickup has its own flow.
- **Database:** Alembic revision `0001_mvp_schema` creates `users`, `lockers`, `compartments`, `parcels`, and `pickup_codes` from the team SQL contract. Serialize UUIDs as strings and use timezone-aware timestamps. Feature services own transactions. `get_db` provides one session per request.
- **Admin (PR #38):** Pass `require_admin` and `get_db` to `AdminLockerController`. Use the shared models in place of its temporary mappings. `Locker.compartments` is ordered by compartment number. The team agreed to the `ADMIN` role.
- **Allocation:** The partial unique index rejects two `ASSIGNED` or `READY_FOR_PICKUP` parcels in the same compartment. Use a single transaction for reserving a compartment and updating the parcel. The feature service still needs to check whether the compartment is available.

- **Pickup (UC4):** `POST /api/terminal/pickup/verify` and `/confirm` (see Schemas-Endpoints §2.5). Migrations: `0002_unique_pickup_code_hash` (from UC3, identical file) then `0003_terminal_lockouts`.
- **Pickup codes (UC3 ↔ UC4):** deposit's `PickupCodeIssuer` and pickup's `PickupCodeHasher` both compute `HMAC-SHA256(PICKUP_CODE_SECRET, pin)` as hex; set `PICKUP_CODE_SECRET` (at least 32 bytes) once in `.env` and build UC3's issuer from `settings.pickup_code_secret`. Pickup returns 503 while it is unset. A collected code's hash is retired so the PIN can be reused under the unique constraint.
- **Terminal credentials:** `require_locker_terminal` (`app.security.terminal_auth`) is the shared kiosk dependency for deposit and pickup. It verifies `Authorization: Bearer <terminal token>` and returns a principal with `locker_id: str`, matching UC3's `TerminalContext`. Issue a token per station with `python -m app.security.terminal_auth <locker_id>` and give it to the terminal UI as `VITE_TERMINAL_TOKEN`. Tokens use their own audience, so staff JWTs and terminal tokens are never interchangeable. Revocation is not implemented yet: rotating `JWT_SECRET` invalidates all of them.

## Integration decisions

- Choose where to terminate HTTPS and verify login and protected routes in the deployed environment for NFR_01.
- Agree when an expired parcel stops blocking reuse, and how to record its physical clearance.
- Terminal-wide lockouts are stored in `terminal_lockouts`. Pickup codes are issued at deposit. Terminals authenticate with per-station signed tokens; per-terminal revocation is still open. The SQL/API contract puts issuance at deposit. The assignment requirements mention earlier issuance.
- Wire the feature routers into the shared application and confirm what database interfaces each module needs.
