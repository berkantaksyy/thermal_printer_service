"""
pytest configuration and shared fixtures.
"""

import os
import asyncio
import pytest
import pytest_asyncio

# Set test environment before importing app
os.environ.setdefault("API_BEARER_TOKEN", "test-token")
os.environ.setdefault("LOG_DIR", "/tmp/thermal_test_logs")
os.environ.setdefault("LLM_ENABLED", "false")

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.printer import set_printer
from tests.mock_printer import MockPrinter


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def client():
    """AsyncClient with Bearer token pre-configured."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": "Bearer test-token"},
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def connected_client():
    """Client with a mock printer already connected."""
    mock = MockPrinter("usb")
    await mock.connect()
    set_printer(mock)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": "Bearer test-token"},
    ) as ac:
        yield ac, mock
    set_printer(None)
