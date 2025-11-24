"""Tests for authentication endpoints."""

import pytest
from fastapi.testclient import TestClient
from main import app
from routes.auth import fake_users_db


@pytest.fixture(autouse=True)
def reset_db():
    """Reset the in-memory database before each test."""
    fake_users_db.clear()
    yield
    fake_users_db.clear()


client = TestClient(app)


def test_health_endpoint():
    """Test /health endpoint returns 200 and status: healthy."""
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_new_user():
    """Test registering a new user returns status 201 and includes access_token."""
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "role": "farmer"
    }
    
    response = client.post("/api/auth/register", json=user_data)
    
    assert response.status_code == 201
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_duplicate_registration():
    """Test duplicate registration returns 400."""
    user_data = {
        "email": "duplicate@example.com",
        "password": "testpassword123",
        "role": "farmer"
    }
    
    # First registration should succeed
    response1 = client.post("/api/auth/register", json=user_data)
    assert response1.status_code == 201
    
    # Second registration with same email should fail
    response2 = client.post("/api/auth/register", json=user_data)
    assert response2.status_code == 400
    assert "already registered" in response2.json()["detail"].lower()


def test_successful_login():
    """Test successful login returns access_token."""
    # First, register a user
    user_data = {
        "email": "login@example.com",
        "password": "testpassword123",
        "role": "farmer"
    }
    client.post("/api/auth/register", json=user_data)
    
    # Now try to login
    login_data = {
        "email": "login@example.com",
        "password": "testpassword123"
    }
    response = client.post("/api/auth/login", json=login_data)
    
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_wrong_password():
    """Test login with wrong password returns 401."""
    # First, register a user
    user_data = {
        "email": "wrongpass@example.com",
        "password": "correctpassword",
        "role": "farmer"
    }
    client.post("/api/auth/register", json=user_data)
    
    # Try to login with wrong password
    login_data = {
        "email": "wrongpass@example.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/auth/login", json=login_data)
    
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()
