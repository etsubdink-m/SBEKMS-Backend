import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    """Test client fixture"""
    return TestClient(app)

@pytest.fixture
def test_settings():
    """Test settings fixture"""
    from app.config import settings
    settings.DEBUG = True
    settings.TRIPLESTORE_URL = "http://localhost:7200"
    return settings 