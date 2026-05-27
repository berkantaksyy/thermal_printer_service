"""
Mock printer for tests — simulates a connected printer without hardware.

Enhanced with error simulation capabilities for all printer error scenarios:
- PAPER_OUT: Paper roll is empty
- PAPER_JAM: Paper is jammed in the mechanism
- COVER_OPEN: Printer cover is open
- OVERHEAT: Printer temperature is too high
- COMM_ERROR: Communication failure
- UNKNOWN_COMMAND: Unsupported ESC/POS command

Usage:
    mock = MockPrinter("usb")
    await mock.connect()
    
    # Simulate paper out error
    mock.simulate_error("PAPER_OUT")
    
    # Or simulate error for next N operations
    mock.simulate_error("PAPER_JAM", operations=3)
    
    # Reset to normal operation
    mock.clear_errors()
"""

from app.core.printer import BasePrinter
from app.core.error_handler import PrinterError, PrinterErrorCode


class MockPrinter(BasePrinter):
    def __init__(self, conn_type: str = "usb"):
        super().__init__()
        self._conn_type = conn_type
        self.written_data: list[bytes] = []
        
        # Error simulation state
        self._error_code: PrinterErrorCode | None = None
        self._error_operations_remaining: int = 0
        self._paper_ok: bool = True
        self._cover_ok: bool = True
        self._temperature_ok: bool = True
        
        # Statistics
        self.write_count: int = 0
        self.error_count: int = 0

    def connection_type(self) -> str:
        return self._conn_type

    async def connect(self) -> None:
        """Simulate printer connection."""
        if self._error_code == PrinterErrorCode.COMM_ERROR:
            self.error_count += 1
            raise PrinterError(
                PrinterErrorCode.COMM_ERROR,
                "Failed to connect to mock printer"
            )
        self._mark_connected()

    async def disconnect(self) -> None:
        """Simulate printer disconnection."""
        self._mark_disconnected()

    async def write(self, data: bytes) -> None:
        """
        Simulate writing data to printer.
        Raises PrinterError if error simulation is active.
        """
        self.write_count += 1
        
        # Check if we should simulate an error
        if self._error_code is not None:
            if self._error_operations_remaining == -1 or self._error_operations_remaining > 0:
                if self._error_operations_remaining > 0:
                    self._error_operations_remaining -= 1
                
                self.error_count += 1
                raise PrinterError(
                    self._error_code,
                    f"Mock printer error: {self._error_code.value}"
                )
        
        # Normal operation - store the data
        self.written_data.append(data)

    async def get_status(self) -> dict:
        """
        Return printer status based on current error simulation state.
        """
        return {
            "paper_ok": self._paper_ok,
            "cover_ok": self._cover_ok,
            "temperature_ok": self._temperature_ok,
            "simulated": True,
            "error_code": self._error_code.value if self._error_code else None,
        }

    def total_bytes_written(self) -> int:
        """Return total bytes successfully written."""
        return sum(len(d) for d in self.written_data)

    # ── Error Simulation Methods ─────────────────────────────────────────────

    def simulate_error(
        self,
        error_code: str | PrinterErrorCode,
        operations: int = -1
    ) -> None:
        """
        Simulate a printer error for the next N operations.
        
        Args:
            error_code: Error code to simulate (PAPER_OUT, PAPER_JAM, etc.)
            operations: Number of operations to fail (-1 = infinite, until cleared)
        
        Examples:
            mock.simulate_error("PAPER_OUT")  # Fail all operations
            mock.simulate_error("PAPER_JAM", operations=3)  # Fail next 3 operations
        """
        if isinstance(error_code, str):
            error_code = PrinterErrorCode(error_code)
        
        self._error_code = error_code
        self._error_operations_remaining = operations
        
        # Update status flags based on error type
        if error_code == PrinterErrorCode.PAPER_OUT:
            self._paper_ok = False
        elif error_code == PrinterErrorCode.PAPER_JAM:
            self._paper_ok = False
        elif error_code == PrinterErrorCode.COVER_OPEN:
            self._cover_ok = False
        elif error_code == PrinterErrorCode.OVERHEAT:
            self._temperature_ok = False

    def simulate_paper_out(self, operations: int = -1) -> None:
        """Simulate paper out error."""
        self.simulate_error(PrinterErrorCode.PAPER_OUT, operations)

    def simulate_paper_jam(self, operations: int = -1) -> None:
        """Simulate paper jam error."""
        self.simulate_error(PrinterErrorCode.PAPER_JAM, operations)

    def simulate_cover_open(self, operations: int = -1) -> None:
        """Simulate cover open error."""
        self.simulate_error(PrinterErrorCode.COVER_OPEN, operations)

    def simulate_overheat(self, operations: int = -1) -> None:
        """Simulate overheat error."""
        self.simulate_error(PrinterErrorCode.OVERHEAT, operations)

    def simulate_comm_error(self, operations: int = -1) -> None:
        """Simulate communication error."""
        self.simulate_error(PrinterErrorCode.COMM_ERROR, operations)

    def simulate_unknown_command(self, operations: int = -1) -> None:
        """Simulate unknown command error."""
        self.simulate_error(PrinterErrorCode.UNKNOWN_COMMAND, operations)

    def clear_errors(self) -> None:
        """Clear all error simulations and reset to normal operation."""
        self._error_code = None
        self._error_operations_remaining = 0
        self._paper_ok = True
        self._cover_ok = True
        self._temperature_ok = True

    def reset_statistics(self) -> None:
        """Reset write and error counters."""
        self.write_count = 0
        self.error_count = 0
        self.written_data.clear()
