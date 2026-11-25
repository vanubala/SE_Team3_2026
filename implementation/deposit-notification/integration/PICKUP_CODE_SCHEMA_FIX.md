# Shared pickup-code uniqueness migration

The shared backend is under `src/backend` on current `main`. UC3 adds a new Alembic migration at `src/backend/migrations/versions/0002_unique_pickup_code_hash.py`, following `0001_mvp_schema`. The migration adds the database constraint `uq_pickup_codes_code_hash`; no existing shared model, migration, or teammate-owned file is edited.

The `PickupCode` ORM mapping already has a `code_hash` column. The migration makes the database enforce hash uniqueness even when two deposit requests race. Keep Alembic migrations enabled when deploying UC3.

Before applying it to a database that may already contain pickup codes, check for duplicate hashes. If duplicates exist, invalidate/reissue those codes before applying the constraint; otherwise Alembic will stop rather than silently discard data.
