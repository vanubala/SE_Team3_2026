"""One engine per application; one database session per request."""
from collections.abc import Iterator
from fastapi import Request
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from app.config import Settings


def make_engine(settings: Settings):
    if make_url(settings.database_url).get_backend_name() != 'postgresql':
        raise ValueError('The MVP runtime requires PostgreSQL; inject a test engine for isolated tests')
    return create_engine(settings.database_url, pool_pre_ping=True)


def get_db(request: Request) -> Iterator[Session]:
    factory: sessionmaker = request.app.state.session_factory
    with factory() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        # The service owns the transaction; closing rolls back unfinished work.
