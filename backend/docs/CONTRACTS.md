# Backend integration notes

- **Authentication:** `POST /api/auth/login` verifies staff passwords with Argon2id and issues a signed JWT. Tokens default to 30 minutes. Use `require_courier`, `require_admin`, or `current_user` on staff routes. Guest pickup has its own flow.
- **Database:** Alembic revision `0001_mvp_schema` creates `users`, `lockers`, `compartments`, `parcels`, and `pickup_codes` from the team SQL contract. Serialize UUIDs as strings and use timezone-aware timestamps. Feature services own transactions. `get_db` provides one session per request.
- **Admin (PR #38):** Pass `require_admin` and `get_db` to `AdminLockerController`. Use the shared models in place of its temporary mappings. `Locker.compartments` is ordered by compartment number. The team agreed to the `ADMIN` role.
- **Allocation:** The partial unique index rejects two `ASSIGNED` or `READY_FOR_PICKUP` parcels in the same compartment. Use a single transaction for reserving a compartment and updating the parcel. The feature service still needs to check whether the compartment is available.

## Integration decisions

- Choose where to terminate HTTPS and verify login and protected routes in the deployed environment for NFR_01.
- Agree when an expired parcel stops blocking reuse, and how to record its physical clearance.
- Agree where to store terminal-wide lockouts, how terminals authenticate, and when to issue pickup codes. The SQL/API contract puts issuance at deposit. The assignment requirements mention earlier issuance.
- Wire the feature routers into the shared application and confirm what database interfaces each module needs.
