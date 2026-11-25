"""Initial MVP relational schema (Schemas-Endpoints.md sections 1.1–1.5).

Revision ID: 0001_mvp_schema
Revises: None
"""
from alembic import op
import sqlalchemy as sa

revision = '0001_mvp_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('users',
        sa.Column('user_id', sa.Uuid(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('company_name', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("role IN ('COURIER','ADMIN')", name='ck_users_role'))
    op.create_index('uq_users_email_lower', 'users', [sa.text('lower(email)')], unique=True)
    op.create_table('lockers',
        sa.Column('locker_id', sa.Uuid(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('address', sa.String(255), nullable=False),
        sa.Column('gps_location', sa.String(100), nullable=False),
        sa.Column('opening_hours', sa.String(100), nullable=False),
        sa.Column('operational_status', sa.String(20), server_default='ONLINE', nullable=False),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.CheckConstraint("operational_status IN ('ONLINE','OFFLINE','MAINTENANCE')", name='ck_lockers_status'))
    op.create_table('compartments',
        sa.Column('compartment_id', sa.Uuid(), primary_key=True),
        sa.Column('locker_id', sa.Uuid(), sa.ForeignKey('lockers.locker_id'), nullable=False),
        sa.Column('compartment_number', sa.Integer(), nullable=False),
        sa.Column('size_category', sa.String(10), nullable=False),
        sa.Column('status', sa.String(20), server_default='AVAILABLE', nullable=False),
        sa.Column('version', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.UniqueConstraint('locker_id','compartment_number',name='uq_compartments_locker_number'),
        sa.CheckConstraint('compartment_number > 0', name='ck_compartments_number'),
        sa.CheckConstraint("size_category IN ('SMALL','MEDIUM','LARGE')", name='ck_compartments_size'),
        sa.CheckConstraint("status IN ('AVAILABLE','RESERVED','OCCUPIED','MAINTENANCE')", name='ck_compartments_status'),
        sa.CheckConstraint('version >= 0', name='ck_compartments_version'))
    op.create_index('ix_compartments_locker_status_size','compartments',['locker_id','status','size_category'])
    op.create_table('parcels',
        sa.Column('parcel_id', sa.Uuid(), primary_key=True),
        sa.Column('tracking_number', sa.String(100), nullable=False, unique=True),
        sa.Column('size_category', sa.String(10), nullable=False),
        sa.Column('status', sa.String(30), nullable=False),
        sa.Column('preferred_locker_id', sa.Uuid(), sa.ForeignKey('lockers.locker_id'), nullable=True),
        sa.Column('compartment_id', sa.Uuid(), sa.ForeignKey('compartments.compartment_id'), nullable=True),
        sa.Column('registered_by_courier_id', sa.Uuid(), sa.ForeignKey('users.user_id'), nullable=False),
        sa.Column('recipient_contact', sa.String(255), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('expected_delivery', sa.DateTime(timezone=True), nullable=True),
        sa.Column('registered_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deposited_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('pickup_deadline', sa.DateTime(timezone=True), nullable=True),
        sa.Column('collected_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("size_category IN ('SMALL','MEDIUM','LARGE')", name='ck_parcels_size'),
        sa.CheckConstraint("status IN ('REGISTERED','ASSIGNED','READY_FOR_PICKUP','COLLECTED','EXPIRED')", name='ck_parcels_status'))
    op.create_index('ix_parcels_courier_status','parcels',['registered_by_courier_id','status'])
    op.create_index('ix_parcels_preferred_locker_id','parcels',['preferred_locker_id'])
    op.create_index('ix_parcels_compartment_id','parcels',['compartment_id'])
    condition = sa.text("compartment_id IS NOT NULL AND status IN ('ASSIGNED','READY_FOR_PICKUP')")
    op.create_index('uq_parcels_active_compartment','parcels',['compartment_id'],unique=True,
                    postgresql_where=condition,sqlite_where=condition)
    op.create_table('pickup_codes',
        sa.Column('code_id', sa.Uuid(), primary_key=True),
        sa.Column('parcel_id', sa.Uuid(), sa.ForeignKey('parcels.parcel_id'), nullable=False, unique=True),
        sa.Column('code_hash', sa.String(255), nullable=False),
        sa.Column('failed_attempts', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('issued_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('failed_attempts >= 0', name='ck_pickup_codes_attempts'))


def downgrade():
    for table in ('pickup_codes','parcels','compartments','lockers','users'):
        op.drop_table(table)
