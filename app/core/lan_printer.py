"""
LAN (Ethernet/TCP) printer backend for Cashino KP-300 / KP-301H.

Communicates via raw TCP socket to printer's built-in network print server.
Default port: 9100 (standard RAW printing port).

KP-300 LAN specs (from datasheet):
  - Interface: RJ45 Ethernet
  - Protocol: TCP/IP Raw printing on port 9100
  - Supports 10/100 Mbps
"""

import asyncio
import logging
from typing import Optional

from app.core.printer import BasePrinter
from app.core.error_handler import PrinterError, PrinterErrorCode
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LanPrinter(BasePrinter):
    """TCP/IP printer backend using asyncio streams."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
    ):
        super().__init__()
        settings = get_settings()
        self._host = host or settings.lan_host
        self._port = port or settings.lan_port
        self._timeout = settings.lan_timeout
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None

    def connection_type(self) -> str:
        return "lan"

    async def connect(self) -> None:
        """Open TCP connection to printer."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=self._timeout,
            )
            self._reader = reader
            self._writer = writer
            self._mark_connected()
            logger.info(f"LAN printer connected to {self._host}:{self._port}")
        except asyncio.TimeoutError:
            raise PrinterError(
                PrinterErrorCode.COMM_ERROR,
                f"Connection to {self._host}:{self._port} timed out after {self._timeout}s.",
            )
        except OSError as exc:
            raise PrinterError(PrinterErrorCode.COMM_ERROR, str(exc))

    async def disconnect(self) -> None:
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
            self._writer = None
            self._reader = None
        self._mark_disconnected()
        logger.info(f"LAN printer disconnected from {self._host}:{self._port}")

    async def write(self, data: bytes) -> None:
        if not self._connected or self._writer is None:
            raise PrinterError(PrinterErrorCode.COMM_ERROR, "LAN printer not connected.")
        try:
            self._writer.write(data)
            await asyncio.wait_for(self._writer.drain(), timeout=self._timeout)
        except (ConnectionResetError, BrokenPipeError, asyncio.TimeoutError) as exc:
            logger.warning(f"LAN write failed: {exc}. Scheduling reconnect.")
            await self.disconnect()
            self.schedule_reconnect()
            raise PrinterError(PrinterErrorCode.COMM_ERROR, f"LAN write error: {exc}")
        except Exception as exc:
            raise PrinterError(PrinterErrorCode.COMM_ERROR, str(exc))

    async def get_status(self) -> dict:
        """
        Send DLE EOT 1 status query and read 1-byte response.
        If unreachable, return degraded status.
        """
        if not self._connected or self._writer is None:
            return {"paper_ok": None, "cover_ok": None, "temperature_ok": None, "simulated": False}

        DLE_EOT_CMD = b"\x10\x04\x01"
        try:
            self._writer.write(DLE_EOT_CMD)
            await asyncio.wait_for(self._writer.drain(), timeout=2.0)
            raw = await asyncio.wait_for(self._reader.read(1), timeout=2.0)
            status_byte = raw[0] if raw else 0

            PAPER_OUT  = 0x20
            COVER_OPEN = 0x04
            OVERHEAT   = 0x40

            return {
                "paper_ok":      not bool(status_byte & PAPER_OUT),
                "cover_ok":      not bool(status_byte & COVER_OPEN),
                "temperature_ok": not bool(status_byte & OVERHEAT),
                "simulated": False,
            }
        except Exception as exc:
            logger.warning(f"LAN status query failed: {exc}")
            return {"paper_ok": None, "cover_ok": None, "temperature_ok": None, "simulated": False}
