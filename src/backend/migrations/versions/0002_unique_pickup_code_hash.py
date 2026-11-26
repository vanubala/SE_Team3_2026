"""Enforce unique stored pickup-code hashes.

Revision ID: 0002_unique_pickup_code_hash
Revises: 0001_mvp_schema
"""
from alembic import op

revision = "0002_unique_pickup_code_hash"
down_revision = "0001_mvp_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("pickup_codes") as batch_op:
        batch_op.create_unique_constraint(
            "uq_pickup_codes_code_hash", ["code_hash"]
        )


def downgrade() -> None:
    with op.batch_alter_table("pickup_codes") as batch_op:
        batch_op.drop_constraint(
            "uq_pickup_codes_code_hash", type_="unique"
        )
