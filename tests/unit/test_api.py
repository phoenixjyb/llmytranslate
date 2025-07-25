"""
Test the translation API endpoints.
"""

import pytest
import asyncio
from httpx import AsyncClient

from src.main import app
from src.services.auth_service import auth_service


@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_supported_languages(client: AsyncClient):
    """Test supported languages endpoint."""
    response = await client.get("/api/languages")
    assert response.status_code == 200
    data = response.json()
    assert "languages" in data
    assert len(data["languages"]) > 0


@pytest.mark.asyncio
async def test_demo_translation(client: AsyncClient):
    """Test demo translation endpoint."""
    response = await client.post(
        "/api/demo/translate",
        data={
            "q": "hello world",
            "from": "en",
            "to": "zh"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "request" in data
    assert "response" in data


@pytest.mark.asyncio
async def test_generate_signature(client: AsyncClient):
    """Test signature generation endpoint."""
    response = await client.get(
        "/api/demo/signature",
        params={
            "q": "hello world",
            "from_lang": "en",
            "to_lang": "zh"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "parameters" in data
    assert "curl_example" in data


@pytest.mark.asyncio
async def test_translation_with_valid_signature(client: AsyncClient):
    """Test translation with properly signed request."""
    # Generate demo request
    demo_request = auth_service.generate_demo_request("hello", "en", "zh")
    
    response = await client.post(
        "/api/trans/vip/translate",
        data=demo_request
    )
    assert response.status_code == 200
    data = response.json()
    assert "trans_result" in data
    assert len(data["trans_result"]) > 0


@pytest.mark.asyncio
async def test_translation_with_invalid_signature(client: AsyncClient):
    """Test translation with invalid signature."""
    response = await client.post(
        "/api/trans/vip/translate",
        data={
            "q": "hello",
            "from": "en",
            "to": "zh",
            "appid": "invalid_app_id",
            "salt": "123456",
            "sign": "invalid_signature"
        }
    )
    assert response.status_code == 200  # API returns 200 with error in body
    data = response.json()
    assert "error_code" in data


def test_auth_service_signature_generation():
    """Test signature generation in auth service."""
    app_id = "test_app"
    query = "hello"
    salt = "123456"
    secret = "test_secret"
    
    signature = auth_service.create_signature(app_id, query, salt, secret)
    assert isinstance(signature, str)
    assert len(signature) == 32  # MD5 hash length


def test_auth_service_signature_verification():
    """Test signature verification."""
    app_id = "test_app"
    query = "hello"
    salt = "123456"
    secret = "test_secret"
    
    # Generate signature
    correct_signature = auth_service.create_signature(app_id, query, salt, secret)
    
    # Test correct signature
    is_valid = auth_service._verify_signature(
        app_id, query, salt, secret, correct_signature
    )
    assert is_valid is True
    
    # Test incorrect signature
    is_valid = auth_service._verify_signature(
        app_id, query, salt, secret, "wrong_signature"
    )
    assert is_valid is False
