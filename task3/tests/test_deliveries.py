"""API tests: delivery endpoints."""

import pytest

from conftest import (
    BASE_URL,
    ALICE_ID, BOB_ID,
    ALICE_TOKEN, BOB_TOKEN,
    ALICE_PACKAGE_ID,
)


def _make_delivery(api, token, sender_id, recipient_id, package_id,
                   address="ул. Тестовая, д. 1, Москва"):
    return api.post(
        f"{BASE_URL}/v1/deliveries",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "sender_id": sender_id,
            "recipient_id": recipient_id,
            "package_id": package_id,
            "address": address,
        },
    )


class TestCreateDelivery:
    def test_create_delivery_returns_201(self, api):
        r = _make_delivery(api, ALICE_TOKEN, ALICE_ID, BOB_ID, ALICE_PACKAGE_ID)
        assert r.status_code == 201
        assert "id" in r.json()
        assert len(r.json()["id"]) == 36

    def test_create_delivery_no_auth_returns_401(self, api):
        r = api.post(f"{BASE_URL}/v1/deliveries", json={
            "sender_id": ALICE_ID,
            "recipient_id": BOB_ID,
            "package_id": ALICE_PACKAGE_ID,
            "address": "addr",
        })
        assert r.status_code == 401

    def test_create_delivery_missing_fields_returns_400(self, api):
        r = api.post(
            f"{BASE_URL}/v1/deliveries",
            headers={"Authorization": f"Bearer {ALICE_TOKEN}"},
            json={"sender_id": ALICE_ID},
        )
        assert r.status_code == 400

    def test_create_delivery_nonexistent_package_returns_400(self, api):
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        r = _make_delivery(api, ALICE_TOKEN, ALICE_ID, BOB_ID, fake_uuid)
        assert r.status_code == 400

    def test_create_delivery_invalid_token_returns_401(self, api):
        r = _make_delivery(api, "totally-invalid-token", ALICE_ID, BOB_ID, ALICE_PACKAGE_ID)
        assert r.status_code == 401


class TestGetDeliveries:
    def test_get_by_sender_returns_list(self, api):
        r = api.get(
            f"{BASE_URL}/v1/deliveries",
            headers={"Authorization": f"Bearer {ALICE_TOKEN}"},
            params={"sender_id": ALICE_ID},
        )
        assert r.status_code == 200
        deliveries = r.json()
        assert isinstance(deliveries, list)
        assert len(deliveries) >= 1

    def test_get_by_sender_all_belong_to_sender(self, api):
        r = api.get(
            f"{BASE_URL}/v1/deliveries",
            headers={"Authorization": f"Bearer {ALICE_TOKEN}"},
            params={"sender_id": ALICE_ID},
        )
        for d in r.json():
            assert d["sender_id"] == ALICE_ID

    def test_get_by_recipient_returns_list(self, api):
        r = api.get(
            f"{BASE_URL}/v1/deliveries",
            headers={"Authorization": f"Bearer {BOB_TOKEN}"},
            params={"recipient_id": BOB_ID},
        )
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) >= 1

    def test_get_by_recipient_all_belong_to_recipient(self, api):
        r = api.get(
            f"{BASE_URL}/v1/deliveries",
            headers={"Authorization": f"Bearer {BOB_TOKEN}"},
            params={"recipient_id": BOB_ID},
        )
        for d in r.json():
            assert d["recipient_id"] == BOB_ID

    def test_delivery_fields_present(self, api):
        r = api.get(
            f"{BASE_URL}/v1/deliveries",
            headers={"Authorization": f"Bearer {ALICE_TOKEN}"},
            params={"sender_id": ALICE_ID},
        )
        d = r.json()[0]
        for field in ("id", "sender_id", "recipient_id", "package_id",
                      "status", "address", "created_at"):
            assert field in d, f"missing field: {field}"

    def test_get_deliveries_no_params_returns_400(self, api):
        r = api.get(
            f"{BASE_URL}/v1/deliveries",
            headers={"Authorization": f"Bearer {ALICE_TOKEN}"},
        )
        assert r.status_code == 400

    def test_get_deliveries_no_auth_returns_401(self, api):
        r = api.get(f"{BASE_URL}/v1/deliveries",
                    params={"sender_id": ALICE_ID})
        assert r.status_code == 401

    def test_create_then_appears_in_sender_list(self, api):
        create_r = _make_delivery(api, ALICE_TOKEN, ALICE_ID, BOB_ID, ALICE_PACKAGE_ID,
                                  address="ул. Уникальная, д. 99")
        assert create_r.status_code == 201
        new_id = create_r.json()["id"]

        list_r = api.get(
            f"{BASE_URL}/v1/deliveries",
            headers={"Authorization": f"Bearer {ALICE_TOKEN}"},
            params={"sender_id": ALICE_ID},
        )
        ids = [d["id"] for d in list_r.json()]
        assert new_id in ids

    def test_create_then_appears_in_recipient_list(self, api):
        create_r = _make_delivery(api, ALICE_TOKEN, ALICE_ID, BOB_ID, ALICE_PACKAGE_ID,
                                  address="ул. Получателя, д. 7")
        assert create_r.status_code == 201
        new_id = create_r.json()["id"]

        list_r = api.get(
            f"{BASE_URL}/v1/deliveries",
            headers={"Authorization": f"Bearer {BOB_TOKEN}"},
            params={"recipient_id": BOB_ID},
        )
        ids = [d["id"] for d in list_r.json()]
        assert new_id in ids
