"""Migrations are explicit; the model metadata is used only for drift checks."""
import os
from logging.config import fileConfig
from alembic import context
from dotenv import load_dotenv
from sqlalchemy import create_engine, pool
from app.db.models import Base

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name, disable_existing_loggers=False)
load_dotenv()
target_metadata = Base.metadata


def migrate(connection):
    context.configure(connection=connection, target_metadata=target_metadata,
                      compare_type=True, compare_server_default=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(url=os.getenv('DATABASE_URL', 'postgresql+psycopg://'),
                      target_metadata=target_metadata, literal_binds=True,
                      dialect_opts={'paramstyle': 'named'})
    with context.begin_transaction():
        context.run_migrations()
elif config.attributes.get('connection') is not None:
    migrate(config.attributes['connection'])
else:
    url = os.getenv('DATABASE_URL')
    if not url:
        raise RuntimeError('Set DATABASE_URL before running migrations')
    engine = create_engine(url, poolclass=pool.NullPool)
    try:
        with engine.connect() as connection:
            migrate(connection)
    finally:
        engine.dispose()
