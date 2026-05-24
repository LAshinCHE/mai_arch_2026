import uuid
import pytest
import requests

BASE_URL = "http://localhost:8083"

ALICE_TOKEN   = "test-token-alice"
BOB_TOKEN     = "test-token-bob"
CHARLIE_TOKEN = "test-token-charlie"


@pytest.fixture(scope="session")
def suffix():
    return uuid.uuid4().hex[:8]


@pytest.fixture(scope="session")
def test_user(suffix):
    login = f"pytest_{suffix}"
    r = requests.post(f"{BASE_URL}/v1/users", json={
        "login":      login,
        "password":   "testpass123",
        "first_name": "Pytest",
        "last_name":  "Runner",
        "email":      f"{login}@test.com",
    })
    assert r.status_code == 201, r.text
    return {"login": login, "password": "testpass123", "id": r.json()["id"]}


@pytest.fixture(scope="session")
def token(test_user):
    r = requests.post(f"{BASE_URL}/v1/auth/login", json={
        "login":    test_user["login"],
        "password": test_user["password"],
    })
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="session")
def alice_id():
    r = requests.get(f"{BASE_URL}/v1/users/search", params={"login": "alice"})
    assert r.status_code == 200
    return r.json()[0]["id"]


@pytest.fixture(scope="session")
def package_id(token):
    r = requests.post(
        f"{BASE_URL}/v1/packages",
        json={"description": "Fixture package", "weight": 0.5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]
