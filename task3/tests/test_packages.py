"""API tests: package endpoints."""

import pytest

from conftest import BASE_URL, ALICE_ID, ALICE_TOKEN, ALICE_PACKAGE_ID


class TestCreatePackage:
    def test_create_package_returns_201(self, api, alice_auth):
        r = api.post(f"{BASE_URL}/v1/packages",
                     headers=alice_auth,
                     json={"description": "Test books", "weight": 1.5})
        assert r.status_code == 201
        body = r.json()
        assert "id" in body
        assert len(body["id"]) == 36

    def test_create_package_zero_weight(self, api, alice_auth):
        r = api.post(f"{BASE_URL}/v1/packages",
                     headers=alice_auth,
                     json={"description": "Envelope", "weight": 0.0})
        assert r.status_code == 201

    def test_create_package_no_auth_returns_401(self, api):
        r = api.post(f"{BASE_URL}/v1/packages",
                     json={"description": "No auth", "weight": 1.0})
        assert r.status_code == 401

    def test_create_package_bad_token_returns_401(self, api):
        r = api.post(f"{BASE_URL}/v1/packages",
                     headers={"Authorization": "Bearer totally-fake-token"},
                     json={"description": "Bad token", "weight": 1.0})
        assert r.status_code == 401

    def test_create_package_missing_auth_header_returns_401(self, api):
        r = api.post(f"{BASE_URL}/v1/packages",
                     headers={"Authorization": "NotBearer abc"},
                     json={"description": "Bad header", "weight": 1.0})
        assert r.status_code == 401


class TestGetUserPackages:
    def test_get_packages_returns_list(self, api, alice_auth):
        r = api.get(f"{BASE_URL}/v1/users/{ALICE_ID}/packages",
                    headers=alice_auth)
        assert r.status_code == 200
        packages = r.json()
        assert isinstance(packages, list)
        assert len(packages) >= 1

    def test_packages_belong_to_user(self, api, alice_auth):
        r = api.get(f"{BASE_URL}/v1/users/{ALICE_ID}/packages",
                    headers=alice_auth)
        for pkg in r.json():
            assert pkg["owner_id"] == ALICE_ID

    def test_package_fields_present(self, api, alice_auth):
        r = api.get(f"{BASE_URL}/v1/users/{ALICE_ID}/packages",
                    headers=alice_auth)
        pkg = r.json()[0]
        for field in ("id", "owner_id", "description", "weight", "status", "created_at"):
            assert field in pkg, f"missing field: {field}"

    def test_get_packages_no_auth_returns_401(self, api):
        r = api.get(f"{BASE_URL}/v1/users/{ALICE_ID}/packages")
        assert r.status_code == 401

    def test_create_then_retrieve_package(self, api, alice_auth):
        description = "Unique test parcel for retrieval"
        create_r = api.post(f"{BASE_URL}/v1/packages",
                            headers=alice_auth,
                            json={"description": description, "weight": 0.123})
        assert create_r.status_code == 201
        new_id = create_r.json()["id"]

        list_r = api.get(f"{BASE_URL}/v1/users/{ALICE_ID}/packages",
                         headers=alice_auth)
        ids = [p["id"] for p in list_r.json()]
        assert new_id in ids
