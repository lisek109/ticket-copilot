import os
import sys
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

# Use a dedicated SQLite database for tests only
os.environ["DATABASE_URL"] = "sqlite:///./test_ticketcopilot.db"

# Make project root importable
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.main import app
from app.db.database import Base, engine


@pytest.fixture(autouse=True)
def reset_db() -> Generator[None, None, None]:
    """
    Reset the test database before each test.
    Keeps tests isolated and reproducible.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """
    Fresh FastAPI test client for each test.
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture()
def register_user(client: TestClient):
    """
    Helper fixture returning a function that registers a user.
    """
    def _register_user(
        email: str = "test@example.com",
        password: str = "StrongPassword123",
        full_name: str = "Test User",
    ) -> dict:
        payload = {
            "email": email,
            "password": password,
            "full_name": full_name,
        }
        response = client.post("/auth/register", json=payload)
        assert response.status_code == 200
        return response.json()

    return _register_user


@pytest.fixture()
def login_user(client: TestClient):
    """
    Helper fixture returning a function that logs in a user and returns a JWT token.
    """
    def _login_user(
        email: str = "test@example.com",
        password: str = "StrongPassword123",
    ) -> str:
        payload = {
            "email": email,
            "password": password,
        }
        response = client.post("/auth/login", json=payload)
        assert response.status_code == 200
        return response.json()["access_token"]

    return _login_user


@pytest.fixture()
def auth_headers(register_user, login_user):
    """
    Helper fixture returning Authorization headers for a freshly registered user.
    """
    def _auth_headers(
        email: str = "test@example.com",
        password: str = "StrongPassword123",
        full_name: str = "Test User",
    ) -> dict:
        register_user(email=email, password=password, full_name=full_name)
        token = login_user(email=email, password=password)
        return {"Authorization": f"Bearer {token}"}

    return _auth_headers