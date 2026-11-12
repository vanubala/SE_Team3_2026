"""Acceptance tests for the shared sign-in rules."""
import sqlite3

import pytest

from app.config import Settings
from app.identifiers import IdentifierKind, InvalidIdentifier, parse_identifier
from app.main import create_app
from fastapi.testclient import TestClient

from conftest import bearer, register, staff_login, wrong


# Recognising what was typed -------------------------------------------------------

@pytest.mark.parametrize("raw, kind, value", [
    ("CO00001", IdentifierKind.COURIER_ID, "CO00001"),
    (" co12345 ", IdentifierKind.COURIER_ID, "CO12345"),
    ("AD00001", IdentifierKind.ADMIN_ID, "AD00001"),
    ("Ana@Example.LU", IdentifierKind.EMAIL, "ana@example.lu"),
    ("co12345@mail.com", IdentifierKind.EMAIL, "co12345@mail.com"),
    ("+352 621 123 456", IdentifierKind.PHONE, "+352621123456"),
    ("00352-621-123-456", IdentifierKind.PHONE, "+352621123456"),
])
def test_identifier_recognition(raw, kind, value):
    parsed = parse_identifier(raw)
    assert (parsed.kind, parsed.value) == (kind, value)


@pytest.mark.parametrize("raw", ["", "CO1234", "CO123456", "AD12A45", "XY00001", "621123456", "ana@", "hello"])
def test_identifier_rejected(raw):
    with pytest.raises(InvalidIdentifier):
        parse_identifier(raw)


# Couriers and administrators --------------------------------------------------

@pytest.mark.parametrize("login_id, role", [("CO00001", "COURIER"), ("AD00001", "ADMINISTRATOR")])
def test_staff_sign_in_with_company_id(client, login_id, role):
    response = staff_login(client, login_id)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["user"]["role"] == role
    assert body["redirect"] == "/dashboard"
    me = client.get("/api/me", headers=bearer(body["token"])).json()
    assert me["loginId"] == login_id and me["role"] == role


def test_staff_id_is_case_insensitive(client):
    assert staff_login(client, "co00002").status_code == 200


def test_wrong_password_and_unknown_id_get_the_same_answer(client):
    wrong_password = staff_login(client, "CO00001", "not-the-password")
    unknown_id = staff_login(client, "CO99999")
    assert wrong_password.status_code == unknown_id.status_code == 401
    assert wrong_password.json() == unknown_id.json()


def test_staff_lockout_after_five_failures(client, clock):
    for _ in range(4):
        assert staff_login(client, "AD00001", "wrong-password").status_code == 401
    fifth = staff_login(client, "AD00001", "wrong-password")
    assert fifth.status_code == 429 and "locked" in fifth.json()["detail"]
    # Even the correct password is refused while locked.
    assert staff_login(client, "AD00001").status_code == 429
    clock.advance(minutes=16)
    assert staff_login(client, "AD00001").status_code == 200


def test_staff_cannot_use_one_time_codes(client):
    response = client.post("/api/auth/code", json={"identifier": "CO00001"})
    assert response.status_code == 400
    assert "company ID and password" in response.json()["detail"]


def test_password_sign_in_is_refused_for_email_and_phone(client):
    for identifier in ["ana@example.com", "+352621123456"]:
        response = client.post("/api/auth/login", json={"identifier": identifier, "password": "whatever1"})
        assert response.status_code == 400


def test_admin_accounts_exist_from_the_start(client):
    token = staff_login(client, "AD00001").json()["token"]
    accounts = client.get("/api/admin/accounts", headers=bearer(token)).json()["accounts"]
    ids = {a["loginId"] for a in accounts}
    assert {"AD00001", "AD00002", "CO00001", "CO00002", "CO00003"} <= ids


def test_random_staff_passwords_when_none_given(tmp_path):
    settings = Settings(database_path=str(tmp_path / "db.sqlite3"))
    app = create_app(settings)
    issued = {a["loginId"]: a["password"] for a in app.state.staff_credentials}
    assert len(set(issued.values())) == len(issued)
    with TestClient(app) as client:
        assert staff_login(client, "AD00002", issued["AD00002"]).status_code == 200


def test_passwords_are_stored_as_hashes(client, settings):
    with sqlite3.connect(settings.database_path) as db:
        stored = db.execute("SELECT password_hash FROM users WHERE login_id = 'CO00001'").fetchone()[0]
    assert stored.startswith("scrypt$") and "Test-Staff-Password-1" not in stored


# Senders and recipients: registration --------------------------------------------

@pytest.mark.parametrize("identifier", ["ana@example.com", "+352 621 123 456"])
def test_register_with_email_or_phone(client, identifier):
    result = register(client, identifier)
    assert result["user"]["role"] == "CUSTOMER"
    assert result["user"]["status"] == "ACTIVE"
    assert result["user"]["loginId"] is None


@pytest.mark.parametrize("identifier", ["CO00009", "co12345", "AD00001", "AD99999", "CO12"])
def test_company_ids_cannot_be_registered(client, identifier):
    response = client.post("/api/auth/register", json={"name": "Mallory", "identifier": identifier})
    assert response.status_code in (403, 422)
    if response.status_code == 403:
        assert "provided by the company" in response.json()["detail"]


def test_role_cannot_be_chosen_at_registration(client):
    response = client.post("/api/auth/register",
                           json={"name": "Mallory", "identifier": "m@example.com", "role": "ADMINISTRATOR"})
    assert response.status_code == 422


def test_database_refuses_customers_with_company_ids(settings, client):
    with sqlite3.connect(settings.database_path) as db, pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO users (user_id, role, login_id, email, name, created_at) "
                   "VALUES ('x', 'CUSTOMER', 'AD12345', 'x@example.com', 'X', '2026-01-01')")


def test_duplicate_registration_is_refused(client):
    register(client, "ana@example.com")
    response = client.post("/api/auth/register", json={"name": "Ana", "identifier": "ANA@example.com"})
    assert response.status_code == 409


def test_unfinished_registration_can_be_restarted(client, clock):
    first = client.post("/api/auth/register", json={"name": "Ana", "identifier": "ana@example.com"}).json()
    clock.advance(seconds=31)
    second = client.post("/api/auth/register", json={"name": "Ana S.", "identifier": "ana@example.com"}).json()
    old = client.post("/api/auth/register/verify", json={"identifier": "ana@example.com", "code": first["devCode"]})
    assert old.status_code == 401
    new = client.post("/api/auth/register/verify", json={"identifier": "ana@example.com", "code": second["devCode"]})
    assert new.status_code == 201 and new.json()["user"]["name"] == "Ana S."


def test_unverified_account_cannot_sign_in(client):
    client.post("/api/auth/register", json={"name": "Ana", "identifier": "ana@example.com"})
    response = client.post("/api/auth/code", json={"identifier": "ana@example.com"})
    assert response.status_code == 200 and "devCode" not in response.json()


# Senders and recipients: sign in --------------------------------------------------

def test_sign_in_with_one_time_code(client, clock):
    register(client, "+352 621 123 456")
    clock.advance(seconds=31)
    sent = client.post("/api/auth/code", json={"identifier": "00352621123456"})
    assert sent.status_code == 200
    body = sent.json()
    assert body["channel"] == "SMS" and "621123456" not in body["destination"]
    result = client.post("/api/auth/code/verify",
                         json={"identifier": "+352621123456", "code": body["devCode"]})
    assert result.status_code == 200
    assert result.json()["user"]["phone"] == "+352621123456"


def test_unknown_contact_gets_the_same_answer(client):
    register(client, "ana@example.com")
    known = client.post("/api/auth/code", json={"identifier": "ana@example.com"}).json()
    unknown = client.post("/api/auth/code", json={"identifier": "nobody@example.com"}).json()
    known.pop("devCode")
    assert known.keys() == unknown.keys()
    assert known["channel"] == unknown["channel"] == "EMAIL"


def test_code_is_single_use(client):
    register(client, "ana@example.com")
    code = client.post("/api/auth/code", json={"identifier": "ana@example.com"}).json()["devCode"]
    first = client.post("/api/auth/code/verify", json={"identifier": "ana@example.com", "code": code})
    second = client.post("/api/auth/code/verify", json={"identifier": "ana@example.com", "code": code})
    assert first.status_code == 200 and second.status_code == 401


def test_code_expires(client, clock):
    register(client, "ana@example.com")
    code = client.post("/api/auth/code", json={"identifier": "ana@example.com"}).json()["devCode"]
    clock.advance(minutes=11)
    response = client.post("/api/auth/code/verify", json={"identifier": "ana@example.com", "code": code})
    assert response.status_code == 401


def test_new_code_needs_a_short_wait(client, clock):
    register(client, "ana@example.com")
    assert client.post("/api/auth/code", json={"identifier": "ana@example.com"}).status_code == 200
    too_soon = client.post("/api/auth/code", json={"identifier": "ana@example.com"})
    assert too_soon.status_code == 429 and "Retry-After" in too_soon.headers
    clock.advance(seconds=31)
    assert client.post("/api/auth/code", json={"identifier": "ana@example.com"}).status_code == 200


def test_code_lockout_after_five_wrong_codes(client, clock):
    register(client, "ana@example.com")
    code = client.post("/api/auth/code", json={"identifier": "ana@example.com"}).json()["devCode"]
    for _ in range(4):
        r = client.post("/api/auth/code/verify", json={"identifier": "ana@example.com", "code": wrong(code)})
        assert r.status_code == 401
    fifth = client.post("/api/auth/code/verify", json={"identifier": "ana@example.com", "code": wrong(code)})
    assert fifth.status_code == 429
    clock.advance(minutes=16)
    # The code sent before the lockout no longer works; a new one is needed.
    stale = client.post("/api/auth/code/verify", json={"identifier": "ana@example.com", "code": code})
    assert stale.status_code == 401
    fresh = client.post("/api/auth/code", json={"identifier": "ana@example.com"}).json()["devCode"]
    ok = client.post("/api/auth/code/verify", json={"identifier": "ana@example.com", "code": fresh})
    assert ok.status_code == 200


def test_codes_not_shown_when_gateway_mode(tmp_path):
    settings = Settings(database_path=str(tmp_path / "db.sqlite3"), show_codes_on_screen=False)
    with TestClient(create_app(settings)) as client:
        response = client.post("/api/auth/register", json={"name": "Ana", "identifier": "ana@example.com"})
        assert response.status_code == 200 and "devCode" not in response.json()


# Role-based access (FR_05) -------------------------------------------------------

def test_each_area_answers_only_to_its_role(client):
    tokens = {
        "COURIER": staff_login(client, "CO00001").json()["token"],
        "ADMINISTRATOR": staff_login(client, "AD00001").json()["token"],
        "CUSTOMER": register(client, "ana@example.com")["token"],
    }
    areas = {"COURIER": "/api/courier/overview", "ADMINISTRATOR": "/api/admin/accounts",
             "CUSTOMER": "/api/customer/overview"}
    for role, token in tokens.items():
        for area_role, path in areas.items():
            expected = 200 if role == area_role else 403
            assert client.get(path, headers=bearer(token)).status_code == expected, (role, path)


def test_admin_account_list_has_no_secrets(client):
    register(client, "ana@example.com")
    token = staff_login(client, "AD00001").json()["token"]
    accounts = client.get("/api/admin/accounts", headers=bearer(token)).json()["accounts"]
    assert any(a["email"] == "ana@example.com" for a in accounts)
    assert all("password_hash" not in a and "passwordHash" not in a for a in accounts)


def test_missing_or_tampered_token_is_rejected(client):
    assert client.get("/api/me").status_code == 401
    token = staff_login(client, "CO00001").json()["token"]
    header, payload, signature = token.split(".")
    tampered = ".".join([header, payload, signature[::-1]])
    assert client.get("/api/me", headers=bearer(tampered)).status_code == 401


def test_token_from_another_server_start_is_rejected(tmp_path, client):
    token = staff_login(client, "CO00001").json()["token"]
    other = Settings(database_path=str(tmp_path / "other.sqlite3"))
    with TestClient(create_app(other)) as other_client:
        assert other_client.get("/api/me", headers=bearer(token)).status_code == 401


# Pages ------------------------------------------------------------------------

def test_pages_are_served_with_security_headers(client):
    for path, text in [("/", "Sign in"), ("/register", "Create an account"), ("/dashboard", "Access check")]:
        response = client.get(path)
        assert response.status_code == 200 and text in response.text
        assert "default-src 'self'" in response.headers["Content-Security-Policy"]
    assert client.get("/static/common.js").status_code == 200
