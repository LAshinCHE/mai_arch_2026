"""API tests: user endpoints."""

import pytest
import requests

from conftest import BASE_URL, ALICE_ID


class TestCreateUser:
    def test_create_returns_201_with_id(self, api, unique_login):
        r = api.post(f"{BASE_URL}/v1/users", json={
            "login": unique_login,
            "password": "pass123",
            "first_name": "Test",
            "last_name": "User",
            "email": f"{unique_login}@test.com",
        })
        assert r.status_code == 201
        body = r.json()
        assert "id" in body
        # must be a non-empty string (UUID format)
        assert len(body["id"]) == 36

    def test_duplicate_login_returns_409(self, api, unique_login):
        payload = {
            "login": unique_login,
            "password": "pass",
            "first_name": "A",
            "last_name": "B",
            "email": f"{unique_login}@test.com",
        }
        api.post(f"{BASE_URL}/v1/users", json=payload)
        r = api.post(f"{BASE_URL}/v1/users", json={**payload, "email": f"other_{unique_login}@test.com"})
        assert r.status_code == 409

    def test_missing_fields_returns_400(self, api):
        r = api.post(f"{BASE_URL}/v1/users", json={"login": "only_login"})
        assert r.status_code == 400

    def test_empty_body_returns_400(self, api):
        r = api.post(f"{BASE_URL}/v1/users", json={})
        assert r.status_code == 400


class TestSearchUsers:
    def test_search_by_exact_login(self, api):
        r = api.get(f"{BASE_URL}/v1/users/search", params={"login": "alice"})
        assert r.status_code == 200
        users = r.json()
        assert len(users) == 1
        assert users[0]["login"] == "alice"
        assert users[0]["id"] == ALICE_ID

    def test_search_by_login_not_found(self, api):
        r = api.get(f"{BASE_URL}/v1/users/search", params={"login": "nobody_xyzxyz"})
        assert r.status_code == 200
        assert r.json() == []

    def test_search_by_name_mask(self, api):
        r = api.get(f"{BASE_URL}/v1/users/search", params={"name": "Ali", "last_name": "Smi"})
        assert r.status_code == 200
        users = r.json()
        assert any(u["first_name"] == "Alice" for u in users)

    def test_search_by_name_case_insensitive(self, api):
        r = api.get(f"{BASE_URL}/v1/users/search", params={"name": "alice", "last_name": "smith"})
        assert r.status_code == 200
        assert len(r.json()) >= 1

    def test_search_no_params_returns_400(self, api):
        r = api.get(f"{BASE_URL}/v1/users/search")
        assert r.status_code == 400

    def test_search_result_fields(self, api):
        r = api.get(f"{BASE_URL}/v1/users/search", params={"login": "alice"})
        user = r.json()[0]
        for field in ("id", "login", "first_name", "last_name", "email"):
            assert field in user, f"missing field: {field}"


class TestLogin:
    def test_login_returns_token_and_user_id(self, api, unique_login):
        api.post(f"{BASE_URL}/v1/users", json={
            "login": unique_login,
            "password": "mypassword",
            "first_name": "X",
            "last_name": "Y",
            "email": f"{unique_login}@t.com",
        })
        r = api.post(f"{BASE_URL}/v1/auth/login",
                     json={"login": unique_login, "password": "mypassword"})
        assert r.status_code == 200
        body = r.json()
        assert "token" in body
        assert "user_id" in body
        assert len(body["token"]) > 0

    def test_wrong_password_returns_401(self, api):
        r = api.post(f"{BASE_URL}/v1/auth/login",
                     json={"login": "alice", "password": "wrong"})
        assert r.status_code == 401

    def test_unknown_login_returns_401(self, api):
        r = api.post(f"{BASE_URL}/v1/auth/login",
                     json={"login": "nobody_xyzxyz", "password": "x"})
        assert r.status_code == 401

    def test_missing_fields_returns_400(self, api):
        r = api.post(f"{BASE_URL}/v1/auth/login", json={"login": "alice"})
        assert r.status_code == 400
