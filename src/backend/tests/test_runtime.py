"""Fail closed, preserve the documented API error format and avoid secret leaks."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from app.config import Settings
from app.db.session import get_db, make_engine
from app.main import create_app
from app.security.dependencies import require_role


def test_non_postgresql_runtime_rejected():
    with pytest.raises(ValueError, match='PostgreSQL'):
        make_engine(Settings(database_url='sqlite+pysqlite://',jwt_secret='test-only-'+'a'*40))


def test_empty_role_guard_fails_closed():
    with pytest.raises(ValueError): require_role()


def test_database_failure_has_safe_envelope():
    engine=create_engine('sqlite+pysqlite://')
    app=create_app(Settings(database_url='sqlite+pysqlite://',jwt_secret='test-only-'+'a'*40),engine=engine)
    def unavailable():
        raise OperationalError('sensitive query',{'secret':'secret-password'},Exception('driver error'))
    app.dependency_overrides[get_db]=unavailable
    try:
        with TestClient(app) as client:
            r=client.post('/api/auth/login',json={'email':'user@example.test','password':'secret-password'})
            assert r.status_code==503
            assert r.json()['error']=='SERVICE_UNAVAILABLE'
            assert set(r.json())=={'timestamp','status','error','message'}
            assert 'secret-password' not in r.text and 'sensitive query' not in r.text
    finally: engine.dispose()
