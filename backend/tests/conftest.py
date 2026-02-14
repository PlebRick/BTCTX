"""
Shared pytest fixtures for BTCTX test suite.

Provides authenticated sessions for tests that hit the live backend API
(router-level auth requires login first).
"""

import pytest
import requests
from fastapi.testclient import TestClient

BASE_URL = "http://127.0.0.1:8000"
LOGIN_CREDS = {"username": "admin", "password": "password"}


@pytest.fixture(scope="session")
def auth_session():
    """Authenticated requests.Session for API tests against live backend."""
    session = requests.Session()
    r = session.post(f"{BASE_URL}/api/login", json=LOGIN_CREDS)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text}"
    return session


@pytest.fixture(scope="session")
def auth_client():
    """Authenticated FastAPI TestClient for in-process tests.

    Ensures admin user exists in the local database before login.
    """
    from backend.main import app
    from backend.database import SessionLocal
    from backend.models.user import User
    import bcrypt

    # Ensure admin user exists (local DB may differ from live backend)
    db = SessionLocal()
    try:
        admin = db.query(User).filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=bcrypt.hashpw(b"password", bcrypt.gensalt()).decode("utf-8"),
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()

    client = TestClient(app)
    r = client.post("/api/login", json=LOGIN_CREDS)
    assert r.status_code == 200, f"TestClient login failed: {r.status_code} {r.text}"
    return client
