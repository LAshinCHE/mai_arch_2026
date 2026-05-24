"""Shared fixtures for delivery service tests."""

import hashlib
import os
import uuid

import psycopg2
import pytest
import requests

BASE_URL = os.getenv("API_URL", "http://localhost:8080")
DB_DSN = os.getenv(
    "DB_CONNECTION",
    "postgresql://delivery:delivery_pass@localhost:5432/delivery_db",
)

# Fixed test users present in data.sql
ALICE_ID = "a0000001-0000-0000-0000-000000000001"
BOB_ID = "a0000001-0000-0000-0000-000000000002"
ALICE_TOKEN = "test-token-alice"
BOB_TOKEN = "test-token-bob"

# Fixed packages present in data.sql
ALICE_PACKAGE_ID = "b0000002-0000-0000-0000-000000000001"
BOB_PACKAGE_ID = "b0000002-0000-0000-0000-000000000003"


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


# ---------------------------------------------------------------------------
# API fixtures
# ---------------------------------------------------------------------------

def _server_available() -> bool:
    try:
        r = requests.get(f"{BASE_URL}/ping", timeout=2)
        return r.status_code == 200
    except requests.exceptions.ConnectionError:
        return False


@pytest.fixture(scope="session")
def api():
    """Returns a requests.Session pre-configured for the API.
    Skips all API tests if the server is not running."""
    if not _server_available():
        pytest.skip("API server not available — run `make up` first")
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="session")
def alice_auth(api):
    """Bearer token for alice (from data.sql pre-seeded token)."""
    return {"Authorization": f"Bearer {ALICE_TOKEN}"}


@pytest.fixture(scope="session")
def bob_auth(api):
    return {"Authorization": f"Bearer {BOB_TOKEN}"}


@pytest.fixture()
def unique_login():
    """Generate a unique login for each test that creates a user."""
    return f"user_{uuid.uuid4().hex[:8]}"


# ---------------------------------------------------------------------------
# DB fixtures
# ---------------------------------------------------------------------------

def _db_available(dsn: str) -> bool:
    try:
        conn = psycopg2.connect(dsn, connect_timeout=3)
        conn.close()
        return True
    except psycopg2.OperationalError:
        return False


@pytest.fixture(scope="session")
def db():
    """psycopg2 connection; skips DB tests if postgres is not reachable."""
    if not _db_available(DB_DSN):
        pytest.skip("PostgreSQL not available — run `make up` first")
    conn = psycopg2.connect(DB_DSN)
    conn.autocommit = True
    yield conn
    conn.close()


@pytest.fixture()
def cur(db):
    """Fresh cursor that rolls back after each test (keeps data clean)."""
    with db.cursor() as c:
        db.autocommit = False
        try:
            yield c
        finally:
            db.rollback()
            db.autocommit = True
