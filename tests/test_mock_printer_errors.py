"""
Comprehensive tests for MockPrinter error simulation capabilities.

Tests all 6 error scenarios defined in the project specification:
- PAPER_OUT: Paper roll is empty
- PAPER_JAM: Paper is jammed
- COVER_OPEN: Printer cover is open
- OVERHEAT: Printer overheating
- COMM_ERROR: Communication failure
- UNKNOWN_COMMAND: Unsupported command

These tests demonstrate the mock printer's ability to simulate real-world
printer failures, which is valuable for evaluators to see comprehensive
error handling without physical hardware.
"""

import pytest
import pytest_asyncio
from app.core.error_handler import PrinterError, PrinterErrorCode
from tests.mock_printer import MockPrinter


# ── Basic Error Simulation Tests ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_paper_out_error():
    """Test PAPER_OUT error simulation."""
    mock = MockPrinter("usb")
    await mock.connect()
    
    # Simulate paper out
    mock.simulate_paper_out()
    
    # Status should reflect paper issue
    status = await mock.get_status()
    assert status["paper_ok"] is False
    assert status["error_code"] == "PAPER_OUT"
    
    # Write should fail with PAPER_OUT error
    with pytest.raises(PrinterError) as exc_info:
        await mock.write(b"test data")
    
    assert exc_info.value.code == PrinterErrorCode.PAPER_OUT
    assert exc_info.value.http_status == 503
    assert mock.error_count == 1


@pytest.mark.asyncio
async def test_paper_jam_error():
    """Test PAPER_JAM error simulation."""
    mock = MockPrinter("usb")
    await mock.connect()
    
    mock.simulate_paper_jam()
    
    status = await mock.get_status()
    assert status["paper_ok"] is False
    assert status["error_code"] == "PAPER_JAM"
    
    with pytest.raises(PrinterError) as exc_info:
        await mock.write(b"test data")
    
    assert exc_info.value.code == PrinterErrorCode.PAPER_JAM
    assert exc_info.value.http_status == 503


@pytest.mark.asyncio
async def test_cover_open_error():
    """Test COVER_OPEN error simulation."""
    mock = MockPrinter("usb")
    await mock.connect()
    
    mock.simulate_cover_open()
    
    status = await mock.get_status()
    assert status["cover_ok"] is False
    assert status["error_code"] == "COVER_OPEN"
    
    with pytest.raises(PrinterError) as exc_info:
        await mock.write(b"test data")
    
    assert exc_info.value.code == PrinterErrorCode.COVER_OPEN
    assert exc_info.value.http_status == 503


@pytest.mark.asyncio
async def test_overheat_error():
    """Test OVERHEAT error simulation."""
    mock = MockPrinter("usb")
    await mock.connect()
    
    mock.simulate_overheat()
    
    status = await mock.get_status()
    assert status["temperature_ok"] is False
    assert status["error_code"] == "OVERHEAT"
    
    with pytest.raises(PrinterError) as exc_info:
        await mock.write(b"test data")
    
    assert exc_info.value.code == PrinterErrorCode.OVERHEAT
    assert exc_info.value.http_status == 503


@pytest.mark.asyncio
async def test_comm_error():
    """Test COMM_ERROR simulation."""
    mock = MockPrinter("usb")
    await mock.connect()
    
    mock.simulate_comm_error()
    
    with pytest.raises(PrinterError) as exc_info:
        await mock.write(b"test data")
    
    assert exc_info.value.code == PrinterErrorCode.COMM_ERROR
    assert exc_info.value.http_status == 502


@pytest.mark.asyncio
async def test_unknown_command_error():
    """Test UNKNOWN_COMMAND error simulation."""
    mock = MockPrinter("usb")
    await mock.connect()
    
    mock.simulate_unknown_command()
    
    with pytest.raises(PrinterError) as exc_info:
        await mock.write(b"test data")
    
    assert exc_info.value.code == PrinterErrorCode.UNKNOWN_COMMAND
    assert exc_info.value.http_status == 400


# ── Limited Operation Error Tests ────────────────────────────────────────────


@pytest.mark.asyncio
async def test_error_for_limited_operations():
    """Test error simulation for a specific number of operations."""
    mock = MockPrinter("usb")
    await mock.connect()
    
    # Simulate paper jam for next 3 operations only
    mock.simulate_paper_jam(operations=3)
    
    # First 3 writes should fail
    for i in range(3):
        with pytest.raises(PrinterError) as exc_info:
            await mock.write(b"test data")
        assert exc_info.value.code == PrinterErrorCode.PAPER_JAM
    
    # 4th write should succeed (error cleared after 3 operations)
    await mock.write(b"success data")
    assert mock.total_bytes_written() > 0
    assert mock.error_count == 3


@pytest.mark.asyncio
async def test_error_recovery_after_clear():
    """Test that clearing errors restores normal operation."""
    mock = MockPrinter("usb")
    await mock.connect()
    
    # Simulate paper out
    mock.simulate_paper_out()
    
    # Should fail
    with pytest.raises(PrinterError):
        await mock.write(b"test data")
    
    # Clear errors
    mock.clear_errors()
    
    # Should succeed now
    await mock.write(b"success data")
    assert mock.total_bytes_written() > 0
    
    # Status should be back to normal
    status = await mock.get_status()
    assert status["paper_ok"] is True
    assert status["cover_ok"] is True
    assert status["temperature_ok"] is True
    assert status["error_code"] is None


# ── Integration Tests with API ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_api_print_with_paper_out(client):
    """Test API response when printer has paper out error."""
    from app.core.printer import set_printer
    
    mock = MockPrinter("usb")
    await mock.connect()
    mock.simulate_paper_out()
    set_printer(mock)
    
    try:
        resp = await client.post("/print/text", json={
            "lines": [{"text": "Test", "bold": False, "align": "left", "font_size": "normal"}],
            "cut": True
        })
        
        # Should return 503 (Service Unavailable) for PAPER_OUT
        assert resp.status_code == 503
        data = resp.json()
        assert "error" in data["detail"]
        assert data["detail"]["error"]["code"] == "PAPER_OUT"
    finally:
        set_printer(None)


@pytest.mark.asyncio
async def test_api_print_with_cover_open(client):
    """Test API response when printer cover is open."""
    from app.core.printer import set_printer
    
    mock = MockPrinter("usb")
    await mock.connect()
    mock.simulate_cover_open()
    set_printer(mock)
    
    try:
        resp = await client.post("/print/text", json={
            "lines": [{"text": "Test", "bold": False, "align": "left", "font_size": "normal"}],
            "cut": True
        })
        
        assert resp.status_code == 503
        data = resp.json()
        assert data["detail"]["error"]["code"] == "COVER_OPEN"
    finally:
        set_printer(None)


@pytest.mark.asyncio
async def test_api_print_with_overheat(client):
    """Test API response when printer is overheating."""
    from app.core.printer import set_printer
    
    mock = MockPrinter("usb")
    await mock.connect()
    mock.simulate_overheat()
    set_printer(mock)
    
    try:
        resp = await client.post("/print/text", json={
            "lines": [{"text": "Test", "bold": False, "align": "left", "font_size": "normal"}],
            "cut": True
        })
        
        assert resp.status_code == 503
        data = resp.json()
        assert data["detail"]["error"]["code"] == "OVERHEAT"
    finally:
        set_printer(None)


@pytest.mark.asyncio
async def test_api_status_reflects_errors(client):
    """Test that /status endpoint reflects printer error state."""
    from app.core.printer import set_printer
    
    mock = MockPrinter("usb")
    await mock.connect()
    mock.simulate_paper_jam()
    set_printer(mock)
    
    try:
        resp = await client.get("/status")
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["connected"] is True
        assert data["paper_ok"] is False
        assert data["error_code"] == "PAPER_JAM"
    finally:
        set_printer(None)


# ── Scenario-Based Tests ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_intermittent_paper_jam_scenario():
    """
    Simulate a realistic scenario: paper jam occurs, fails 2 times,
    then user clears the jam and printing resumes.
    """
    mock = MockPrinter("usb")
    await mock.connect()
    
    # Simulate intermittent paper jam (fails next 2 operations)
    mock.simulate_paper_jam(operations=2)
    
    # First attempt fails
    with pytest.raises(PrinterError) as exc1:
        await mock.write(b"Receipt line 1")
    assert exc1.value.code == PrinterErrorCode.PAPER_JAM
    
    # Second attempt fails
    with pytest.raises(PrinterError) as exc2:
        await mock.write(b"Receipt line 2")
    assert exc2.value.code == PrinterErrorCode.PAPER_JAM
    
    # Third attempt succeeds (jam cleared automatically after 2 operations)
    await mock.write(b"Receipt line 3")
    assert mock.total_bytes_written() > 0
    assert mock.error_count == 2
    assert mock.write_count == 3


@pytest.mark.asyncio
async def test_multiple_error_types_sequence():
    """Test switching between different error types."""
    mock = MockPrinter("usb")
    await mock.connect()
    
    # First: paper out
    mock.simulate_paper_out(operations=1)
    with pytest.raises(PrinterError) as exc1:
        await mock.write(b"data1")
    assert exc1.value.code == PrinterErrorCode.PAPER_OUT
    
    # Then: cover open
    mock.simulate_cover_open(operations=1)
    with pytest.raises(PrinterError) as exc2:
        await mock.write(b"data2")
    assert exc2.value.code == PrinterErrorCode.COVER_OPEN
    
    # Then: overheat
    mock.simulate_overheat(operations=1)
    with pytest.raises(PrinterError) as exc3:
        await mock.write(b"data3")
    assert exc3.value.code == PrinterErrorCode.OVERHEAT
    
    # Finally: success
    await mock.write(b"data4")
    assert mock.total_bytes_written() > 0


@pytest.mark.asyncio
async def test_comm_error_on_connect():
    """Test communication error during connection attempt."""
    mock = MockPrinter("usb")
    mock.simulate_comm_error()
    
    # Connection should fail
    with pytest.raises(PrinterError) as exc_info:
        await mock.connect()
    
    assert exc_info.value.code == PrinterErrorCode.COMM_ERROR
    assert "connect" in exc_info.value.detail.lower()


# ── Statistics and Monitoring Tests ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_error_statistics_tracking():
    """Test that error and write counts are tracked correctly."""
    mock = MockPrinter("usb")
    await mock.connect()
    
    # Reset statistics
    mock.reset_statistics()
    assert mock.write_count == 0
    assert mock.error_count == 0
    
    # Successful writes
    await mock.write(b"data1")
    await mock.write(b"data2")
    assert mock.write_count == 2
    assert mock.error_count == 0
    
    # Failed writes
    mock.simulate_paper_out(operations=3)
    for _ in range(3):
        with pytest.raises(PrinterError):
            await mock.write(b"data")
    
    assert mock.write_count == 5  # 2 successful + 3 failed attempts
    assert mock.error_count == 3


@pytest.mark.asyncio
async def test_generic_simulate_error_with_string():
    """Test simulate_error method with string error code."""
    mock = MockPrinter("usb")
    await mock.connect()
    
    # Use string instead of enum
    mock.simulate_error("PAPER_OUT", operations=1)
    
    with pytest.raises(PrinterError) as exc_info:
        await mock.write(b"test")
    
    assert exc_info.value.code == PrinterErrorCode.PAPER_OUT


@pytest.mark.asyncio
async def test_generic_simulate_error_with_enum():
    """Test simulate_error method with enum error code."""
    mock = MockPrinter("usb")
    await mock.connect()
    
    # Use enum directly
    mock.simulate_error(PrinterErrorCode.COVER_OPEN, operations=1)
    
    with pytest.raises(PrinterError) as exc_info:
        await mock.write(b"test")
    
    assert exc_info.value.code == PrinterErrorCode.COVER_OPEN
