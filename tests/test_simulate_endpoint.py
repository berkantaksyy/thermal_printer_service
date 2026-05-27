"""
Test simulate endpoint functionality.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient

from app.core.printer import set_printer
from tests.mock_printer import MockPrinter


@pytest.mark.asyncio
async def test_simulate_endpoint_paper_out(client: AsyncClient):
    """Test /simulate endpoint with PAPER_OUT error"""
    # Setup mock printer
    mock = MockPrinter("usb")
    await mock.connect()
    set_printer(mock)
    
    try:
        # Activate PAPER_OUT simulation
        resp = await client.post("/simulate", json={
            "error_type": "PAPER_OUT",
            "operations": -1
        })
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "activated"
        assert data["error_type"] == "PAPER_OUT"
        assert data["operations"] == -1
        
        # Check simulation status
        status_resp = await client.get("/simulate/status")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["simulation_active"] is True
        assert status_data["current_error"] == "PAPER_OUT"
        assert status_data["is_mock_printer"] is True
        
        # Try to print - should fail with 503
        print_resp = await client.post("/print/text", json={
            "lines": [{"text": "Test", "bold": False, "align": "left", "font_size": "normal"}],
            "cut": True
        })
        assert print_resp.status_code == 503
        
        # Clear simulation
        clear_resp = await client.post("/simulate", json={
            "error_type": None,
            "operations": 0
        })
        assert clear_resp.status_code == 200
        assert clear_resp.json()["status"] == "cleared"
        
        # Check simulation is cleared
        status_resp2 = await client.get("/simulate/status")
        assert status_resp2.json()["simulation_active"] is False
        
    finally:
        set_printer(None)


@pytest.mark.asyncio
async def test_simulate_endpoint_limited_operations(client: AsyncClient):
    """Test /simulate endpoint with limited operations"""
    mock = MockPrinter("usb")
    await mock.connect()
    set_printer(mock)
    
    try:
        # Activate simulation for 2 operations
        resp = await client.post("/simulate", json={
            "error_type": "PAPER_JAM",
            "operations": 2
        })
        
        assert resp.status_code == 200
        assert resp.json()["operations"] == 2
        
        # First print should fail
        resp1 = await client.post("/print/text", json={
            "lines": [{"text": "Test 1", "bold": False, "align": "left", "font_size": "normal"}],
            "cut": False
        })
        assert resp1.status_code == 503
        
        # Second print should fail
        resp2 = await client.post("/print/text", json={
            "lines": [{"text": "Test 2", "bold": False, "align": "left", "font_size": "normal"}],
            "cut": False
        })
        assert resp2.status_code == 503
        
        # Third print should succeed (simulation cleared after 2 operations)
        resp3 = await client.post("/print/text", json={
            "lines": [{"text": "Test 3", "bold": False, "align": "left", "font_size": "normal"}],
            "cut": False
        })
        assert resp3.status_code == 200
        
    finally:
        set_printer(None)


@pytest.mark.asyncio
async def test_simulate_endpoint_no_printer(client: AsyncClient):
    """Test /simulate endpoint when no printer is connected"""
    set_printer(None)
    
    resp = await client.post("/simulate", json={
        "error_type": "PAPER_OUT",
        "operations": -1
    })
    
    assert resp.status_code == 502


@pytest.mark.asyncio
async def test_simulate_status_no_printer(client: AsyncClient):
    """Test /simulate/status when no printer is connected"""
    set_printer(None)
    
    resp = await client.get("/simulate/status")
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["simulation_active"] is False
    assert data["is_mock_printer"] is False


@pytest.mark.asyncio
async def test_simulate_all_error_types(client: AsyncClient):
    """Test all error types can be simulated"""
    mock = MockPrinter("usb")
    await mock.connect()
    set_printer(mock)
    
    error_types = [
        "PAPER_OUT",
        "PAPER_JAM",
        "COVER_OPEN",
        "OVERHEAT",
        "COMM_ERROR",
        "UNKNOWN_COMMAND"
    ]
    
    try:
        for error_type in error_types:
            # Activate error
            resp = await client.post("/simulate", json={
                "error_type": error_type,
                "operations": 1
            })
            
            assert resp.status_code == 200
            assert resp.json()["error_type"] == error_type
            
            # Verify it's active
            status = await client.get("/simulate/status")
            assert status.json()["current_error"] == error_type
            
            # Try to print - should fail
            print_resp = await client.post("/print/text", json={
                "lines": [{"text": "Test", "bold": False, "align": "left", "font_size": "normal"}],
                "cut": False
            })
            
            # UNKNOWN_COMMAND returns 400, others return 503 or 502
            assert print_resp.status_code in [400, 502, 503]
            
    finally:
        # Clear and cleanup
        await client.post("/simulate", json={"error_type": None})
        set_printer(None)
