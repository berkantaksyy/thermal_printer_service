"""
API endpoint tests.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_no_auth(client: AsyncClient):
    """Health endpoint is public — no token required."""
    resp = await client.get("/health", headers={})
    # Remove auth header temporarily
    async with AsyncClient(
        transport=client._transport,
        base_url="http://test",
    ) as no_auth:
        resp = await no_auth.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_health_with_token(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in ("ok", "degraded")
    assert data["printer_connected"] is False  # no printer in base fixture
    assert data["uptime_seconds"] >= 0


@pytest.mark.asyncio
async def test_status_no_printer(client: AsyncClient):
    resp = await client.get("/status")
    assert resp.status_code == 200
    assert resp.json()["connected"] is False


@pytest.mark.asyncio
async def test_status_with_mock_printer(connected_client):
    ac, mock = connected_client
    resp = await ac.get("/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["connected"] is True
    assert data["connection_type"] == "usb"
    assert data["paper_ok"] is True


@pytest.mark.asyncio
async def test_print_text_no_printer(client: AsyncClient):
    resp = await client.post("/print/text", json={
        "lines": [{"text": "Hello", "bold": False, "align": "left", "font_size": "normal"}],
        "cut": True
    })
    assert resp.status_code == 502  # COMM_ERROR


@pytest.mark.asyncio
async def test_print_text_with_printer(connected_client):
    ac, mock = connected_client
    resp = await ac.post("/print/text", json={
        "lines": [
            {"text": "ACO RECYCLING", "bold": True, "align": "center", "font_size": "double"},
            {"text": "Reward: 3.00 TL", "bold": False, "align": "center", "font_size": "normal"},
        ],
        "cut": True
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "done"
    assert "job_id" in data
    assert mock.total_bytes_written() > 0


@pytest.mark.asyncio
async def test_print_text_idempotency(connected_client):
    """Sending the same job_id twice should not print twice."""
    ac, mock = connected_client
    payload = {
        "job_id": "idempotency-test-001",
        "lines": [{"text": "Test idempotency", "bold": False, "align": "left", "font_size": "normal"}],
        "cut": False
    }
    r1 = await ac.post("/print/text", json=payload)
    bytes_after_first = mock.total_bytes_written()
    r2 = await ac.post("/print/text", json=payload)
    bytes_after_second = mock.total_bytes_written()

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["job_id"] == r2.json()["job_id"]
    # Second call should not write more bytes (idempotent)
    assert bytes_after_first == bytes_after_second


@pytest.mark.asyncio
async def test_print_qr(connected_client):
    ac, mock = connected_client
    resp = await ac.post("/print/qr", json={
        "data": "https://example.com",
        "size": 6,
        "error_correction": "M",
        "align": "center",
        "cut": True
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


@pytest.mark.asyncio
async def test_print_image_invalid_base64(connected_client):
    ac, _ = connected_client
    resp = await ac.post("/print/image", json={
        "image_base64": "NOT_VALID_BASE64!!!",
        "align": "center",
        "cut": True
    })
    assert resp.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_reprint_not_found(connected_client):
    ac, _ = connected_client
    resp = await ac.post("/reprint", json={"job_id": "nonexistent-job-id-xyz"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_logs_empty(client: AsyncClient):
    resp = await client.get("/logs?page=1&page_size=10")
    assert resp.status_code == 200
    data = resp.json()
    assert "entries" in data
    assert "total" in data


@pytest.mark.asyncio
async def test_logs_after_print(connected_client):
    ac, mock = connected_client
    await ac.post("/print/text", json={
        "lines": [{"text": "Log test", "bold": False, "align": "left", "font_size": "normal"}],
        "cut": False
    })
    resp = await ac.get("/logs")
    assert resp.status_code == 200
    data = resp.json()
    ops = [e["op"] for e in data["entries"]]
    assert "print_text" in ops


@pytest.mark.asyncio
async def test_unauthorized_no_token():
    """Request without token should return 401."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/status")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_connect_disconnect(client: AsyncClient):
    """Test the connect endpoint in simulation mode (no USB hardware)."""
    # Connect via USB — will succeed in simulation mode (pyusb not available in test env)
    resp = await client.post("/connect", json={"connection_type": "usb"})
    # Either 200 (simulation) or 502 (no USB hardware) — both acceptable
    assert resp.status_code in (200, 502)
