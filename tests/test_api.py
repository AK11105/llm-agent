import pytest
from fastapi import status
from httpx import AsyncClient
from httpx import ASGITransport
from main import app

# Use a valid secret from your config
VALID_SECRET = "super_secret_token"
INVALID_SECRET = "wrong_secret"

@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_build_endpoint_valid_secret():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        payload = {
            "secret": VALID_SECRET,
            "project_name": "test_build_app",
            "brief": {"goal": "Create a hello world app"}
        }
        response = await client.post("/build", json=payload)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["status"] == "build_and_deploy_complete"
        assert "repo_url" in json_data
        assert "pages_url" in json_data

@pytest.mark.asyncio
async def test_build_endpoint_invalid_secret():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        payload = {
            "secret": INVALID_SECRET,
            "project_name": "test_invalid_secret",
            "brief": {"goal": "Create a hello world app"}
        }
        response = await client.post("/build", json=payload)
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.asyncio
async def test_revise_endpoint_valid_secret():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        payload = {
            "secret": VALID_SECRET,
            "project_name": "phase4_test_app",
            "brief": {"goal": "Add new feature"},
            "repo_url": "https://github.com/AK11105/phase4_test_app.git",
            "changes": ["add_new_feature"]
        }
        response = await client.post("/revise", json=payload)
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["status"] == "revision_complete"
        assert "updated_files" in json_data
