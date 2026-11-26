"""HTTP tests against the contract in Schemas-Endpoints.md."""
import uuid
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from pydantic.alias_generators import to_snake
from sqlalchemy.exc import OperationalError

from app.main import create_app
from register_assign.support import NAMESPACE, auth, uid

BELVAL = str(uid("loc-belval-01"))
PARCEL = {
    "trackingNumber": "LU-987654321",
    "sizeCategory": "MEDIUM",
    "preferredLockerId": BELVAL,
    "recipientContact": "recipient@example.lu",
    "expectedDelivery": "2099-11-20T14:00:00Z",
    "notes": "Handle with care",
}
ERROR_BODY = {"timestamp", "status", "error", "message"}


def register(client, courier="courier-1", **changes) -> dict:
    response = client.post("/api/parcels", json={**PARCEL, **changes}, headers=auth(courier=courier))
    assert response.status_code == 201, response.json()
    return response.json()


def test_register_answers_201_with_the_agreed_fields(client, belval):
    body = register(client)

    assert set(body) == {"parcelId", "trackingNumber", "status", "preferredLockerId", "registeredAt"}
    assert body["status"] == "REGISTERED"
    assert body["registeredAt"].endswith("Z")


def test_errors_use_the_agreed_error_body(client, belval):
    response = client.post("/api/parcels", json={**PARCEL, "sizeCategory": "XL"}, headers=auth())

    assert response.status_code == 400
    assert set(response.json()) == ERROR_BODY
    assert response.json()["error"] == "BAD_REQUEST"


@pytest.mark.parametrize("body", [
    pytest.param({"trackingNumber": "LU-1"}, id="missing-fields"),
    pytest.param({**PARCEL, "status": "COLLECTED"}, id="field-the-client-may-not-set"),
    pytest.param({**PARCEL, "registeredByCourierId": "courier-9"}, id="another-courier"),
    pytest.param({to_snake(name): value for name, value in PARCEL.items()}, id="snake-case-names"),
])
def test_malformed_or_extra_fields_answer_400(client, belval, body):
    response = client.post("/api/parcels", json=body, headers=auth())

    assert response.status_code == 400
    assert set(response.json()) == ERROR_BODY


def test_body_that_is_not_json_answers_400(client):
    headers = {**auth(), "Content-Type": "application/json"}

    response = client.post("/api/parcels", content="{not json", headers=headers)

    assert response.status_code == 400
    assert set(response.json()) == ERROR_BODY


def test_duplicate_tracking_number_answers_409(client, belval):
    register(client)

    response = client.post("/api/parcels", json=PARCEL, headers=auth())

    assert response.status_code == 409
    assert response.json()["error"] == "CONFLICT"


@pytest.mark.parametrize("headers, status", [
    pytest.param({}, 401, id="no-token"),
    pytest.param({"Authorization": "Basic Y291cmllcjpwYXNz"}, 401, id="not-a-bearer-token"),
    pytest.param(auth(expires_in=timedelta(seconds=-1)), 401, id="expired"),
    pytest.param(auth(secret="another-secret-of-at-least-32-bytes"), 401, id="forged-signature"),
    pytest.param(auth(algorithm="HS512"), 401, id="algorithm-not-allowed"),
    pytest.param(auth(iss="someone-else"), 401, id="wrong-issuer"),
    pytest.param(auth(aud="another-api"), 401, id="wrong-audience"),
    pytest.param(auth(role=None), 401, id="no-role"),
    pytest.param(auth(sub=" "), 401, id="empty-user"),
    pytest.param(auth(sub="courier-1"), 401, id="user-id-not-a-uuid"),
    pytest.param(auth(role="ADMIN"), 403, id="not-a-courier"),
])
def test_only_couriers_with_a_valid_token_get_in(client, belval, headers, status):
    for response in (
        client.post("/api/parcels", json=PARCEL, headers=headers),
        client.get(f"/api/lockers/{BELVAL}/compartments?size=SMALL", headers=headers),
    ):
        assert response.status_code == status
        assert set(response.json()) == ERROR_BODY
    if status == 401:
        assert response.headers["WWW-Authenticate"] == "Bearer"


def test_token_signed_with_alg_none_is_refused(client, belval):
    unsigned = auth(secret=None, algorithm="none")

    assert client.post("/api/parcels", json=PARCEL, headers=unsigned).status_code == 401


def test_lists_registered_parcels_with_the_agreed_fields(client, belval):
    register(client)

    response = client.get("/api/parcels?status=REGISTERED", headers=auth())

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert set(response.json()[0]) == {
        "parcelId", "trackingNumber", "sizeCategory", "status", "preferredLockerId", "expectedDelivery"
    }
    assert response.json()[0]["expectedDelivery"] == "2099-11-20T14:00:00Z"


def test_available_compartments_with_recommendation(client, belval):
    response = client.get(f"/api/lockers/{BELVAL}/compartments?size=MEDIUM", headers=auth())

    assert response.status_code == 200
    assert response.json() == {
        "lockerId": BELVAL,
        "recommendedCompartmentId": str(uid("comp-04")),
        "availableCompartments": [
            {"compartmentId": str(uid("comp-04")), "compartmentNumber": 4, "sizeCategory": "MEDIUM"},
            {"compartmentId": str(uid("comp-09")), "compartmentNumber": 9, "sizeCategory": "LARGE"},
        ],
    }


def test_assign_answers_200_then_409_for_the_same_compartment(client, belval):
    first = register(client, trackingNumber="LU-1")
    second = register(client, trackingNumber="LU-2")
    choice = {"lockerId": BELVAL, "compartmentId": str(uid("comp-04"))}

    ok = client.post(f"/api/parcels/{first['parcelId']}/assign", json=choice, headers=auth())
    taken = client.post(f"/api/parcels/{second['parcelId']}/assign", json=choice, headers=auth())

    assert ok.status_code == 200
    assert ok.json() == {
        "parcelId": first["parcelId"],
        "status": "ASSIGNED",
        "lockerId": BELVAL,
        "compartmentId": str(uid("comp-04")),
        "compartmentNumber": 4,
    }
    assert taken.status_code == 409
    assert taken.json()["message"] == "Compartment no longer available"


def test_assign_unknown_parcel_answers_404(client, belval):
    choice = {"lockerId": BELVAL, "compartmentId": str(uid("comp-04"))}

    response = client.post(f"/api/parcels/{uid('no-such-parcel')}/assign", json=choice, headers=auth())

    assert response.status_code == 404


@pytest.mark.parametrize("method, path, body", [
    pytest.param("POST", "/api/parcels", {**PARCEL, "preferredLockerId": "loc-belval-01"}, id="preferred-locker"),
    pytest.param("GET", "/api/lockers/loc-belval-01/compartments?size=SMALL", None, id="locker-in-path"),
    pytest.param("POST", "/api/parcels/p-1/assign", {"lockerId": BELVAL, "compartmentId": str(uid("comp-04"))},
                 id="parcel-in-path"),
    pytest.param("POST", f"/api/parcels/{uid('no-such-parcel')}/assign",
                 {"lockerId": BELVAL, "compartmentId": "comp-04"}, id="compartment-in-body"),
])
def test_an_id_that_is_not_a_uuid_answers_400(client, belval, method, path, body):
    response = client.request(method, path, json=body, headers=auth())

    assert response.status_code == 400
    assert set(response.json()) == ERROR_BODY


def test_another_couriers_parcel_answers_404_like_a_missing_one(client, belval):
    parcel = register(client, courier="courier-2")
    choice = {"lockerId": BELVAL, "compartmentId": str(uid("comp-04"))}

    response = client.post(f"/api/parcels/{parcel['parcelId']}/assign", json=choice, headers=auth(courier="courier-1"))

    assert response.status_code == 404
    assert response.json()["message"] == "Parcel not found"
    still_free = client.get(f"/api/lockers/{BELVAL}/compartments?size=MEDIUM", headers=auth())
    assert still_free.json()["recommendedCompartmentId"] == str(uid("comp-04"))


@pytest.mark.parametrize("method, path, status", [
    pytest.param("GET", "/api/no-such-route", 404, id="unknown-route"),
    pytest.param("DELETE", "/api/parcels", 405, id="method-not-allowed"),
])
def test_framework_errors_use_the_agreed_error_body(client, method, path, status):
    response = client.request(method, path, headers=auth())

    assert response.status_code == status
    assert set(response.json()) == ERROR_BODY


def test_a_database_failure_answers_503_without_internal_details(settings, engine, monkeypatch):
    def broken(*args, **kwargs):
        raise OperationalError("SELECT secret internal detail", {}, Exception("connection lost"))

    monkeypatch.setattr("app.repositories.parcel_repository.ParcelRepository.find_by_courier", broken)
    with TestClient(create_app(settings, engine=engine)) as client:
        response = client.get("/api/parcels", headers=auth())

    assert response.status_code == 503
    assert set(response.json()) == ERROR_BODY
    assert "secret" not in response.text


def test_parcel_ids_are_hashed_with_the_configured_namespace(client, belval):
    body = register(client)

    assert body["parcelId"] == str(uuid.uuid5(NAMESPACE, PARCEL["trackingNumber"]))


def test_without_a_configured_namespace_a_random_one_is_used(settings, engine, belval):
    without = settings.model_copy(update={"parcel_id_namespace": None})
    with TestClient(create_app(without, engine=engine)) as client:
        body = register(client)

    assert body["parcelId"] != str(uuid.uuid5(NAMESPACE, PARCEL["trackingNumber"]))
