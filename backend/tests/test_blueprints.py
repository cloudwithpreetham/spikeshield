import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.models.blueprint import WorkloadProfile

@pytest.mark.asyncio
async def test_generate_upi_blueprint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/blueprints/generate", json={"profile": WorkloadProfile.HIGH_CONCURRENCY_UPI.value})
    assert response.status_code == 200
    data = response.json()
    assert "nginx_config" in data
    assert "procfile" in data

@pytest.mark.asyncio
async def test_generate_edtech_blueprint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/blueprints/generate", json={"profile": WorkloadProfile.EDTECH_RESULT_PORTAL.value})
    assert response.status_code == 200
    data = response.json()
    assert "ebextension_capacity" in data
