"""DB-level unit tests: schema constraints, indexes, and direct SQL queries."""

import hashlib
import uuid

import psycopg2
import pytest

from conftest import ALICE_ID, BOB_ID, ALICE_PACKAGE_ID


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def new_id() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Helper: insert a user directly into DB
# ---------------------------------------------------------------------------
def insert_user(cur, login=None, first_name="Test", last_name="User",
                email=None, password="pass"):
    login = login if login is not None else f"u_{uuid.uuid4().hex[:8]}"
    email = email if email is not None else f"{login}@test.com"
    cur.execute(
        "INSERT INTO delivery.users(login, password_hash, first_name, last_name, email) "
        "VALUES(%s, %s, %s, %s, %s) RETURNING id::text",
        (login, sha256(password), first_name, last_name, email),
    )
    return cur.fetchone()[0]


def insert_package(cur, owner_id, description="Pkg", weight=1.0, status="created"):
    cur.execute(
        "INSERT INTO delivery.packages(owner_id, description, weight, status) "
        "VALUES(%s::uuid, %s, %s, %s) RETURNING id::text",
        (owner_id, description, weight, status),
    )
    return cur.fetchone()[0]


def insert_delivery(cur, sender_id, recipient_id, package_id, address="addr"):
    cur.execute(
        "INSERT INTO delivery.deliveries(sender_id, recipient_id, package_id, address) "
        "VALUES(%s::uuid, %s::uuid, %s::uuid, %s) RETURNING id::text",
        (sender_id, recipient_id, package_id, address),
    )
    return cur.fetchone()[0]


# ---------------------------------------------------------------------------
# Schema: index existence
# ---------------------------------------------------------------------------

class TestIndexes:
    INDEX_NAMES = [
        "idx_users_login",
        "idx_users_name",
        "idx_users_first_name_trgm",
        "idx_users_last_name_trgm",
        "idx_packages_owner",
        "idx_packages_status",
        "idx_packages_owner_active",
        "idx_deliveries_sender",
        "idx_deliveries_recipient",
        "idx_deliveries_created_at",
        "idx_deliveries_sender_status",
        "idx_deliveries_recipient_status",
        "idx_auth_tokens_user",
        "idx_auth_tokens_expires",
    ]

    @pytest.mark.parametrize("index_name", INDEX_NAMES)
    def test_index_exists(self, db, index_name):
        with db.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM pg_indexes WHERE schemaname = 'delivery' AND indexname = %s",
                (index_name,),
            )
            assert cur.fetchone() is not None, f"Index {index_name!r} not found"


# ---------------------------------------------------------------------------
# Schema: constraint tests
# ---------------------------------------------------------------------------

class TestUserConstraints:
    def test_unique_login_rejected(self, cur):
        login = f"dup_{uuid.uuid4().hex[:6]}"
        insert_user(cur, login=login, email=f"a_{login}@t.com")
        with pytest.raises(psycopg2.errors.UniqueViolation):
            insert_user(cur, login=login, email=f"b_{login}@t.com")

    def test_unique_email_rejected(self, cur):
        email = f"{uuid.uuid4().hex}@test.com"
        insert_user(cur, login=f"u1_{uuid.uuid4().hex[:6]}", email=email)
        with pytest.raises(psycopg2.errors.UniqueViolation):
            insert_user(cur, login=f"u2_{uuid.uuid4().hex[:6]}", email=email)

    def test_empty_login_rejected(self, cur):
        with pytest.raises(psycopg2.errors.CheckViolation):
            insert_user(cur, login="")

    def test_empty_first_name_rejected(self, cur):
        with pytest.raises(psycopg2.errors.CheckViolation):
            insert_user(cur, first_name="")

    def test_email_without_at_rejected(self, cur):
        with pytest.raises(psycopg2.errors.CheckViolation):
            insert_user(cur, email="notanemail")


class TestPackageConstraints:
    def test_negative_weight_rejected(self, cur):
        uid = insert_user(cur)
        with pytest.raises(psycopg2.errors.CheckViolation):
            insert_package(cur, owner_id=uid, weight=-1.0)

    def test_invalid_status_rejected(self, cur):
        uid = insert_user(cur)
        with pytest.raises(psycopg2.errors.CheckViolation):
            insert_package(cur, owner_id=uid, status="unknown_status")

    def test_nonexistent_owner_rejected(self, cur):
        with pytest.raises(psycopg2.errors.ForeignKeyViolation):
            insert_package(cur, owner_id=str(uuid.uuid4()))

    def test_cascade_delete_with_user(self, cur):
        uid = insert_user(cur)
        pkg_id = insert_package(cur, owner_id=uid)
        cur.execute("DELETE FROM delivery.users WHERE id = %s::uuid", (uid,))
        cur.execute("SELECT id FROM delivery.packages WHERE id = %s::uuid", (pkg_id,))
        assert cur.fetchone() is None  # CASCADE deleted


class TestDeliveryConstraints:
    def test_sender_equals_recipient_rejected(self, cur):
        uid = insert_user(cur)
        pkg_id = insert_package(cur, owner_id=uid)
        with pytest.raises(psycopg2.errors.CheckViolation):
            insert_delivery(cur, sender_id=uid, recipient_id=uid, package_id=pkg_id)

    def test_empty_address_rejected(self, cur):
        uid1 = insert_user(cur)
        uid2 = insert_user(cur)
        pkg_id = insert_package(cur, owner_id=uid1)
        with pytest.raises(psycopg2.errors.CheckViolation):
            insert_delivery(cur, sender_id=uid1, recipient_id=uid2,
                            package_id=pkg_id, address="")

    def test_invalid_status_rejected(self, cur):
        uid1 = insert_user(cur)
        uid2 = insert_user(cur)
        pkg_id = insert_package(cur, owner_id=uid1)
        with pytest.raises(psycopg2.errors.CheckViolation):
            cur.execute(
                "INSERT INTO delivery.deliveries"
                "(sender_id, recipient_id, package_id, address, status) "
                "VALUES(%s::uuid, %s::uuid, %s::uuid, %s, %s)",
                (uid1, uid2, pkg_id, "addr", "bad_status"),
            )

    def test_nonexistent_package_rejected(self, cur):
        uid1 = insert_user(cur)
        uid2 = insert_user(cur)
        with pytest.raises(psycopg2.errors.ForeignKeyViolation):
            insert_delivery(cur, sender_id=uid1, recipient_id=uid2,
                            package_id=str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# SQL query correctness tests (the 8 API operations)
# ---------------------------------------------------------------------------

class TestUserQueries:
    def test_search_by_login(self, cur):
        login = f"srch_{uuid.uuid4().hex[:8]}"
        insert_user(cur, login=login)
        cur.execute(
            "SELECT id::text, login FROM delivery.users WHERE login = %s", (login,)
        )
        row = cur.fetchone()
        assert row is not None
        assert row[1] == login

    def test_search_by_login_returns_empty_for_unknown(self, cur):
        cur.execute(
            "SELECT id FROM delivery.users WHERE login = %s", ("nobody_xyzxyz_99",)
        )
        assert cur.fetchone() is None

    def test_search_by_name_mask_ilike(self, cur):
        login = f"ilike_{uuid.uuid4().hex[:6]}"
        insert_user(cur, login=login, first_name="Zephyr", last_name="Quorra")
        cur.execute(
            "SELECT id::text FROM delivery.users "
            "WHERE first_name ILIKE %s AND last_name ILIKE %s",
            ("%eph%", "%uorr%"),
        )
        assert cur.fetchone() is not None

    def test_search_ilike_case_insensitive(self, cur):
        login = f"ci_{uuid.uuid4().hex[:6]}"
        insert_user(cur, login=login, first_name="Xander", last_name="Yates")
        cur.execute(
            "SELECT id::text FROM delivery.users "
            "WHERE first_name ILIKE %s AND last_name ILIKE %s",
            ("%xander%", "%YATES%"),
        )
        assert cur.fetchone() is not None

    def test_insert_user_and_retrieve(self, cur):
        login = f"ins_{uuid.uuid4().hex[:8]}"
        uid = insert_user(cur, login=login, first_name="Foo", last_name="Bar")
        cur.execute("SELECT login, first_name, last_name FROM delivery.users WHERE id = %s::uuid", (uid,))
        row = cur.fetchone()
        assert row == (login, "Foo", "Bar")


class TestPackageQueries:
    def test_create_and_get_package(self, cur):
        uid = insert_user(cur)
        pkg_id = insert_package(cur, owner_id=uid, description="My box", weight=3.14)
        cur.execute(
            "SELECT description, weight FROM delivery.packages WHERE id = %s::uuid",
            (pkg_id,),
        )
        row = cur.fetchone()
        assert row[0] == "My box"
        assert float(row[1]) == pytest.approx(3.14, rel=1e-3)

    def test_get_packages_by_owner(self, cur):
        uid = insert_user(cur)
        insert_package(cur, owner_id=uid, description="Pkg A")
        insert_package(cur, owner_id=uid, description="Pkg B")
        cur.execute(
            "SELECT COUNT(*) FROM delivery.packages WHERE owner_id = %s::uuid", (uid,)
        )
        assert cur.fetchone()[0] == 2

    def test_packages_from_other_user_not_returned(self, cur):
        uid1 = insert_user(cur)
        uid2 = insert_user(cur)
        insert_package(cur, owner_id=uid2, description="Other user pkg")
        cur.execute(
            "SELECT COUNT(*) FROM delivery.packages WHERE owner_id = %s::uuid", (uid1,)
        )
        assert cur.fetchone()[0] == 0

    def test_default_status_is_created(self, cur):
        uid = insert_user(cur)
        pkg_id = insert_package(cur, owner_id=uid)
        cur.execute("SELECT status FROM delivery.packages WHERE id = %s::uuid", (pkg_id,))
        assert cur.fetchone()[0] == "created"


class TestDeliveryQueries:
    def _setup(self, cur):
        sender_id = insert_user(cur)
        recipient_id = insert_user(cur)
        pkg_id = insert_package(cur, owner_id=sender_id)
        return sender_id, recipient_id, pkg_id

    def test_create_delivery(self, cur):
        sender_id, recipient_id, pkg_id = self._setup(cur)
        delivery_id = insert_delivery(cur, sender_id, recipient_id, pkg_id, "Test addr 1")
        assert delivery_id is not None
        assert len(delivery_id) == 36

    def test_get_deliveries_by_sender(self, cur):
        sender_id, recipient_id, pkg_id = self._setup(cur)
        insert_delivery(cur, sender_id, recipient_id, pkg_id)
        cur.execute(
            "SELECT COUNT(*) FROM delivery.deliveries WHERE sender_id = %s::uuid",
            (sender_id,),
        )
        assert cur.fetchone()[0] == 1

    def test_get_deliveries_by_recipient(self, cur):
        sender_id, recipient_id, pkg_id = self._setup(cur)
        insert_delivery(cur, sender_id, recipient_id, pkg_id)
        cur.execute(
            "SELECT COUNT(*) FROM delivery.deliveries WHERE recipient_id = %s::uuid",
            (recipient_id,),
        )
        assert cur.fetchone()[0] == 1

    def test_deliveries_by_sender_excludes_other_senders(self, cur):
        sender_id, recipient_id, pkg_id = self._setup(cur)
        other_sender, _, other_pkg = self._setup(cur)
        insert_delivery(cur, other_sender, recipient_id, other_pkg)
        cur.execute(
            "SELECT COUNT(*) FROM delivery.deliveries WHERE sender_id = %s::uuid",
            (sender_id,),
        )
        assert cur.fetchone()[0] == 0

    def test_default_status_is_pending(self, cur):
        sender_id, recipient_id, pkg_id = self._setup(cur)
        delivery_id = insert_delivery(cur, sender_id, recipient_id, pkg_id)
        cur.execute(
            "SELECT status FROM delivery.deliveries WHERE id = %s::uuid", (delivery_id,)
        )
        assert cur.fetchone()[0] == "pending"

    def test_delivery_stores_correct_address(self, cur):
        sender_id, recipient_id, pkg_id = self._setup(cur)
        address = "ул. Тестовая, д. 42, Москва"
        delivery_id = insert_delivery(cur, sender_id, recipient_id, pkg_id, address)
        cur.execute(
            "SELECT address FROM delivery.deliveries WHERE id = %s::uuid", (delivery_id,)
        )
        assert cur.fetchone()[0] == address


class TestAuthTokenQueries:
    def test_valid_token_returns_user_id(self, cur):
        uid = insert_user(cur)
        token = f"tok_{uuid.uuid4().hex}"
        cur.execute(
            "INSERT INTO delivery.auth_tokens(token, user_id) VALUES(%s, %s::uuid)",
            (token, uid),
        )
        cur.execute(
            "SELECT user_id::text FROM delivery.auth_tokens "
            "WHERE token = %s AND expires_at > NOW()",
            (token,),
        )
        assert cur.fetchone()[0] == uid

    def test_expired_token_not_returned(self, cur):
        uid = insert_user(cur)
        token = f"exp_{uuid.uuid4().hex}"
        cur.execute(
            "INSERT INTO delivery.auth_tokens(token, user_id, expires_at) "
            "VALUES(%s, %s::uuid, NOW() - INTERVAL '1 hour')",
            (token, uid),
        )
        cur.execute(
            "SELECT user_id FROM delivery.auth_tokens "
            "WHERE token = %s AND expires_at > NOW()",
            (token,),
        )
        assert cur.fetchone() is None

    def test_cascade_delete_removes_tokens(self, cur):
        uid = insert_user(cur)
        token = f"del_{uuid.uuid4().hex}"
        cur.execute(
            "INSERT INTO delivery.auth_tokens(token, user_id) VALUES(%s, %s::uuid)",
            (token, uid),
        )
        cur.execute("DELETE FROM delivery.users WHERE id = %s::uuid", (uid,))
        cur.execute("SELECT token FROM delivery.auth_tokens WHERE token = %s", (token,))
        assert cur.fetchone() is None
