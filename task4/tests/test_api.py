import uuid
import requests
import pytest

from conftest import BASE_URL, ALICE_TOKEN


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_ping():
    r = requests.get(f"{BASE_URL}/ping")
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# POST /v1/users
# ---------------------------------------------------------------------------

class TestCreateUser:
    def test_returns_201_and_object_id(self, suffix):
        login = f"new_{suffix}_a"
        r = requests.post(f"{BASE_URL}/v1/users", json={
            "login":      login,
            "password":   "pass",
            "first_name": "New",
            "last_name":  "User",
            "email":      f"{login}@x.com",
        })
        assert r.status_code == 201
        body = r.json()
        assert "id" in body
        assert len(body["id"]) == 24          # MongoDB ObjectId — 24 hex символа

    def test_duplicate_login_returns_409(self, suffix):
        login = f"dup_{suffix}"
        payload = {
            "login": login, "password": "p",
            "first_name": "A", "last_name": "B", "email": f"{login}@x.com",
        }
        requests.post(f"{BASE_URL}/v1/users", json=payload)
        r = requests.post(f"{BASE_URL}/v1/users", json=payload)
        assert r.status_code == 409

    def test_duplicate_email_returns_409(self, suffix):
        email = f"same_{suffix}@x.com"
        base = {"password": "p", "first_name": "A", "last_name": "B", "email": email}
        requests.post(f"{BASE_URL}/v1/users", json={**base, "login": f"u1_{suffix}"})
        r = requests.post(f"{BASE_URL}/v1/users", json={**base, "login": f"u2_{suffix}"})
        assert r.status_code == 409

    def test_missing_required_fields_returns_400(self):
        r = requests.post(f"{BASE_URL}/v1/users", json={"login": "incomplete"})
        assert r.status_code == 400

    def test_empty_body_returns_400(self):
        r = requests.post(f"{BASE_URL}/v1/users", json={})
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# POST /v1/auth/login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_correct_credentials(self, test_user):
        r = requests.post(f"{BASE_URL}/v1/auth/login", json={
            "login":    test_user["login"],
            "password": test_user["password"],
        })
        assert r.status_code == 200
        body = r.json()
        assert "token" in body
        assert "user_id" in body
        assert body["user_id"] == test_user["id"]

    def test_token_is_non_empty_string(self, test_user):
        r = requests.post(f"{BASE_URL}/v1/auth/login", json={
            "login":    test_user["login"],
            "password": test_user["password"],
        })
        assert r.status_code == 200
        assert isinstance(r.json()["token"], str)
        assert len(r.json()["token"]) > 0

    def test_wrong_password_returns_401(self, test_user):
        r = requests.post(f"{BASE_URL}/v1/auth/login", json={
            "login":    test_user["login"],
            "password": "definitelywrong",
        })
        assert r.status_code == 401

    def test_unknown_login_returns_401(self):
        r = requests.post(f"{BASE_URL}/v1/auth/login", json={
            "login": "no_such_user_xyzxyz",
            "password": "pass",
        })
        assert r.status_code == 401

    def test_missing_password_returns_400(self):
        r = requests.post(f"{BASE_URL}/v1/auth/login", json={"login": "alice"})
        assert r.status_code == 400

    def test_preseeded_alice(self):
        r = requests.post(f"{BASE_URL}/v1/auth/login", json={
            "login": "alice", "password": "secret",
        })
        assert r.status_code == 200

    def test_preseeded_bob(self):
        r = requests.post(f"{BASE_URL}/v1/auth/login", json={
            "login": "bob", "password": "12345",
        })
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# GET /v1/users/search
# ---------------------------------------------------------------------------

class TestSearchUsers:
    def test_by_exact_login(self):
        r = requests.get(f"{BASE_URL}/v1/users/search", params={"login": "alice"})
        assert r.status_code == 200
        users = r.json()
        assert len(users) == 1
        assert users[0]["login"] == "alice"
        assert "id" in users[0]
        assert "email" in users[0]

    def test_by_login_not_found_returns_empty_list(self):
        r = requests.get(f"{BASE_URL}/v1/users/search", params={"login": "nobody_xyz"})
        assert r.status_code == 200
        assert r.json() == []

    def test_password_hash_not_in_response(self):
        r = requests.get(f"{BASE_URL}/v1/users/search", params={"login": "alice"})
        assert r.status_code == 200
        assert "password_hash" not in r.json()[0]

    def test_by_name_mask(self):
        r = requests.get(f"{BASE_URL}/v1/users/search", params={"name": "Ali", "last_name": "Smi"})
        assert r.status_code == 200
        assert any(u["login"] == "alice" for u in r.json())

    def test_by_name_case_insensitive(self):
        r = requests.get(f"{BASE_URL}/v1/users/search", params={"name": "ali", "last_name": "smi"})
        assert r.status_code == 200
        assert len(r.json()) > 0

    def test_no_params_returns_400(self):
        r = requests.get(f"{BASE_URL}/v1/users/search")
        assert r.status_code == 400

    def test_newly_registered_user_is_searchable(self, test_user):
        r = requests.get(f"{BASE_URL}/v1/users/search", params={"login": test_user["login"]})
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["id"] == test_user["id"]


# ---------------------------------------------------------------------------
# POST /v1/packages
# ---------------------------------------------------------------------------

class TestCreatePackage:
    def test_success(self, token):
        r = requests.post(
            f"{BASE_URL}/v1/packages",
            json={"description": "Laptop", "weight": 1.8},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 201
        assert "id" in r.json()
        assert len(r.json()["id"]) == 24

    def test_no_auth_returns_401(self):
        r = requests.post(f"{BASE_URL}/v1/packages", json={"description": "x", "weight": 1.0})
        assert r.status_code == 401

    def test_invalid_token_returns_401(self):
        r = requests.post(
            f"{BASE_URL}/v1/packages",
            json={"description": "x", "weight": 1.0},
            headers={"Authorization": "Bearer fake_token_that_doesnt_exist"},
        )
        assert r.status_code == 401

    def test_malformed_auth_header_returns_401(self):
        r = requests.post(
            f"{BASE_URL}/v1/packages",
            json={"description": "x", "weight": 1.0},
            headers={"Authorization": "NotBearer token"},
        )
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# GET /v1/users/{id}/packages
# ---------------------------------------------------------------------------

class TestGetUserPackages:
    def test_returns_list(self, test_user, token, package_id):
        r = requests.get(
            f"{BASE_URL}/v1/users/{test_user['id']}/packages",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_created_package_appears_in_list(self, test_user, token, package_id):
        r = requests.get(
            f"{BASE_URL}/v1/users/{test_user['id']}/packages",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        ids = [p["id"] for p in r.json()]
        assert package_id in ids

    def test_package_has_expected_fields(self, test_user, token):
        r = requests.get(
            f"{BASE_URL}/v1/users/{test_user['id']}/packages",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        pkg = r.json()[0]
        assert "id" in pkg
        assert "description" in pkg
        assert "weight" in pkg
        assert "status" in pkg

    def test_no_auth_returns_401(self, test_user):
        r = requests.get(f"{BASE_URL}/v1/users/{test_user['id']}/packages")
        assert r.status_code == 401

    def test_alice_has_preseeded_packages(self, alice_id):
        r = requests.get(
            f"{BASE_URL}/v1/users/{alice_id}/packages",
            headers={"Authorization": f"Bearer {ALICE_TOKEN}"},
        )
        assert r.status_code == 200
        assert len(r.json()) >= 2   # из data.js у alice 2 посылки


# ---------------------------------------------------------------------------
# POST /v1/deliveries
# ---------------------------------------------------------------------------

class TestCreateDelivery:
    def test_success(self, token, test_user, alice_id, package_id):
        r = requests.post(
            f"{BASE_URL}/v1/deliveries",
            json={
                "sender_id":    test_user["id"],
                "recipient_id": alice_id,
                "package_id":   package_id,
                "address":      "ул. Ленина, д. 1, Москва",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 201
        assert "id" in r.json()
        assert len(r.json()["id"]) == 24

    def test_no_auth_returns_401(self, test_user, alice_id, package_id):
        r = requests.post(
            f"{BASE_URL}/v1/deliveries",
            json={
                "sender_id":    test_user["id"],
                "recipient_id": alice_id,
                "package_id":   package_id,
                "address":      "ул. Пушкина, д. 5",
            },
        )
        assert r.status_code == 401

    def test_invalid_object_ids_returns_400(self, token):
        r = requests.post(
            f"{BASE_URL}/v1/deliveries",
            json={
                "sender_id":    "not_an_object_id",
                "recipient_id": "also_bad",
                "package_id":   "bad",
                "address":      "ул. Мира, д. 1",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 400

    def test_missing_address_returns_400(self, token, test_user, alice_id, package_id):
        r = requests.post(
            f"{BASE_URL}/v1/deliveries",
            json={
                "sender_id":    test_user["id"],
                "recipient_id": alice_id,
                "package_id":   package_id,
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 400

    def test_empty_body_returns_400(self, token):
        r = requests.post(
            f"{BASE_URL}/v1/deliveries",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 400


# ---------------------------------------------------------------------------
# GET /v1/deliveries
# ---------------------------------------------------------------------------

class TestGetDeliveries:
    @pytest.fixture(autouse=True)
    def _seed_delivery(self, token, test_user, alice_id, package_id):
        requests.post(
            f"{BASE_URL}/v1/deliveries",
            json={
                "sender_id":    test_user["id"],
                "recipient_id": alice_id,
                "package_id":   package_id,
                "address":      "ул. Тестовая, д. 99",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    def test_by_sender_id(self, token, test_user):
        r = requests.get(
            f"{BASE_URL}/v1/deliveries",
            params={"sender_id": test_user["id"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        deliveries = r.json()
        assert len(deliveries) > 0
        assert all(d["sender_id"] == test_user["id"] for d in deliveries)

    def test_by_recipient_id(self, token, alice_id):
        r = requests.get(
            f"{BASE_URL}/v1/deliveries",
            params={"recipient_id": alice_id},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) > 0

    def test_delivery_has_expected_fields(self, token, test_user):
        r = requests.get(
            f"{BASE_URL}/v1/deliveries",
            params={"sender_id": test_user["id"]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        d = r.json()[0]
        for field in ("id", "sender_id", "recipient_id", "package_id", "address", "status"):
            assert field in d, f"missing field: {field}"

    def test_no_params_returns_400(self, token):
        r = requests.get(
            f"{BASE_URL}/v1/deliveries",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 400

    def test_no_auth_returns_401(self, test_user):
        r = requests.get(
            f"{BASE_URL}/v1/deliveries",
            params={"sender_id": test_user["id"]},
        )
        assert r.status_code == 401

    def test_preseeded_deliveries_exist(self, alice_id):
        r = requests.get(
            f"{BASE_URL}/v1/deliveries",
            params={"recipient_id": alice_id},
            headers={"Authorization": f"Bearer {ALICE_TOKEN}"},
        )
        assert r.status_code == 200
        assert len(r.json()) >= 1
