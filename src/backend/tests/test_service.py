"""Unit tests of business rules with a controlled repository double."""
from unittest.mock import Mock
from uuid import uuid4
import pytest
from app.config import Settings
from app.db.models import Role
from app.repositories.user_repository import UserCredentials
from app.security.passwords import hash_password
from app.security.tokens import TokenService
from app.services.auth_service import AuthService, InvalidCredentials


@pytest.fixture(scope='module')
def password_hash():
    return hash_password('correct-password')


@pytest.mark.parametrize('role', ['COURIER','ADMIN'])
def test_service_uses_repository_and_issues_principal(password_hash,role):
    uid=uuid4()
    users=Mock(); users.find_by_email.return_value=UserCredentials(uid,'Test staff',role,password_hash)
    tokens=Mock(); tokens.issue.return_value='signed-test-token'
    service=AuthService(users,tokens,password_hash)
    result=service.login(' Test@Example.test ','correct-password')
    users.find_by_email.assert_called_once_with('test@example.test')
    tokens.issue.assert_called_once_with(uid,Role(role))
    assert result.token=='signed-test-token' and result.user_id==uid and result.role==Role(role)


@pytest.mark.parametrize('case',['unknown','wrong_password','unsupported_role'])
def test_failure_does_not_issue_token(password_hash,case):
    users=Mock(); tokens=Mock()
    users.find_by_email.return_value=None if case=='unknown' else UserCredentials(uuid4(),'Test staff','RECIPIENT' if case=='unsupported_role' else 'COURIER',password_hash)
    service=AuthService(users,tokens,password_hash)
    with pytest.raises(InvalidCredentials):
        service.login('test@example.test','wrong' if case=='wrong_password' else 'correct-password')
    tokens.issue.assert_not_called()


def test_short_or_placeholder_jwt_secret_rejected():
    from pydantic import ValidationError
    for bad in ['short','replace-with-'+'a'*50]:
        with pytest.raises(ValidationError):
            Settings(database_url='sqlite+pysqlite://',jwt_secret=bad)
