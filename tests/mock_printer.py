"""
Mock printer for tests — simulates a connected printer without hardware.
"""

from app.core.printer import BasePrinter


class MockPrinter(BasePrinter):
    def __init__(self, conn_type: str = "usb"):
        super().__init__()
        self._conn_type = conn_type
        self.written_data: list[bytes] = []
        self.should_fail: bool = False
        self.fail_error = None

    def connection_type(self) -> str:
        return self._conn_type

    async def connect(self) -> None:
        self._mark_connected()

    async def disconnect(self) -> None:
        self._mark_disconnected()

    async def write(self, data: bytes) -> None:
        if self.should_fail:
            from app.core.error_handler import PrinterError
            raise self.fail_error or PrinterError(
                __import__('app.core.error_handler', fromlist=['PrinterErrorCode']).PrinterErrorCode.COMM_ERROR,
                "Mock printer failure"
            )
        self.written_data.append(data)

    async def get_status(self) -> dict:
        return {"paper_ok": True, "cover_ok": True, "temperature_ok": True, "simulated": True}

    def total_bytes_written(self) -> int:
        return sum(len(d) for d in self.written_data)
