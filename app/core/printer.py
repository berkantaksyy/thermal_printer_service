"""
Abstract printer base class and connection factory.
"""

import abc
import asyncio
import time
import logging
from typing import Optional

from app.core.error_handler import PrinterError, PrinterErrorCode
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class BasePrinter(abc.ABC):
    """Abstract interface all printer backends must implement."""

    def __init__(self):
        self._connected: bool = False
        self._connect_time: Optional[float] = None
        self._reconnect_task: Optional[asyncio.Task] = None

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def uptime_seconds(self) -> float:
        if self._connect_time is None:
            return 0.0
        return time.monotonic() - self._connect_time

    @abc.abstractmethod
    async def connect(self) -> None:
        """Establish connection to printer."""

    @abc.abstractmethod
    async def disconnect(self) -> None:
        """Gracefully disconnect from printer."""

    @abc.abstractmethod
    async def write(self, data: bytes) -> None:
        """Send raw bytes to printer."""

    @abc.abstractmethod
    async def get_status(self) -> dict:
        """Query printer status (paper, cover, temperature)."""

    @abc.abstractmethod
    def connection_type(self) -> str:
        """Return 'usb' or 'lan'."""

    async def _start_reconnect_loop(self) -> None:
        """Background task: exponential backoff reconnect."""
        settings = get_settings()
        attempt = 0
        while not self._connected:
            attempt += 1
            if attempt > settings.reconnect_max_retries:
                logger.error("Max reconnect attempts reached. Giving up.")
                break
            delay = min(
                settings.reconnect_backoff_base ** attempt,
                settings.reconnect_backoff_max,
            )
            logger.info(f"Reconnect attempt {attempt} in {delay:.1f}s …")
            await asyncio.sleep(delay)
            try:
                await self.connect()
                logger.info("Reconnect successful.")
            except Exception as exc:
                logger.warning(f"Reconnect attempt {attempt} failed: {exc}")

    def schedule_reconnect(self) -> None:
        """Schedule background reconnect loop (call on disconnect)."""
        if self._reconnect_task and not self._reconnect_task.done():
            return
        loop = asyncio.get_event_loop()
        self._reconnect_task = loop.create_task(self._start_reconnect_loop())

    def _mark_connected(self) -> None:
        self._connected = True
        self._connect_time = time.monotonic()

    def _mark_disconnected(self) -> None:
        self._connected = False


class PrinterFactory:
    """Creates the appropriate printer backend based on connection type."""

    @staticmethod
    def create(connection_type: str, **kwargs) -> "BasePrinter":
        from app.core.usb_printer import UsbPrinter
        from app.core.lan_printer import LanPrinter

        if connection_type == "usb":
            return UsbPrinter(**kwargs)
        elif connection_type == "lan":
            return LanPrinter(**kwargs)
        else:
            raise ValueError(f"Unsupported connection type: {connection_type}")


# Global printer state managed by the service
_current_printer: Optional[BasePrinter] = None


def get_printer() -> Optional[BasePrinter]:
    return _current_printer


def set_printer(printer: Optional[BasePrinter]) -> None:
    global _current_printer
    _current_printer = printer


def require_printer() -> BasePrinter:
    """Return connected printer or raise PrinterError."""
    p = get_printer()
    if p is None or not p.connected:
        raise PrinterError(
            code=PrinterErrorCode.COMM_ERROR,
            detail="No printer connected. Call POST /connect first.",
        )
    return p
