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
    user = User(name="Test User")
    assert user.name == "Test User"

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}