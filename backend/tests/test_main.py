import pytest
from backend.models.user import User
from backend.main import app
from fastapi.testclient import TestClient


def test_hello_world():
    assert 1 + 1 == 2


def test_user_model():
    user = User(username="testuser", password_hash="dummy_hash")
    assert user.username == "testuser"


def test_read_main(auth_client):
    response = auth_client.get("/api/accounts/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)