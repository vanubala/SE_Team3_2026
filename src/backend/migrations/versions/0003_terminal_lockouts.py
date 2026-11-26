"""Terminal-wide pickup lockout state (NFR_02).

Revision ID: 0003_terminal_lockouts
Revises: 0002_unique_pickup_code_hash
"""
from alembic import op
import sqlalchemy as sa

revision = '0003_terminal_lockouts'
down_revision = '0002_unique_pickup_code_hash'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('terminal_lockouts',
        sa.Column('locker_id', sa.Uuid(), sa.ForeignKey('lockers.locker_id'), primary_key=True),
        sa.Column('failed_attempts', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('last_failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('failed_attempts >= 0', name='ck_terminal_lockouts_attempts'))


def downgrade():
    op.drop_table('terminal_lockouts')
