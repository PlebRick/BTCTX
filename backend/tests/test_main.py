import os
print("PYTHONPATH:", os.getenv('PYTHONPATH'))

import pytest
from backend.models.user import User  # Example import, adjust as needed
from backend.main import app  # Example import, adjust as needed
from fastapi.testclient import TestClient

# Initialize the TestClient with your FastAPI app
client = TestClient(app)

def test_hello_world():
    assert 1 + 1 == 2

def test_user_model():
    user = User(username="testuser", password_hash="dummy_hash")
    assert user.username == "testuser"

def test_read_main():
    # Root serves the React frontend (HTML), test an API endpoint instead
    response = client.get("/api/accounts/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)