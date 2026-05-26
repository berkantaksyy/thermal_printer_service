"""
USB printer backend for Cashino KP-300 / KP-301H.

Uses pyusb for direct USB communication.
Vendor ID / Product ID are configurable via Settings.

USB descriptor info (from KP-300 datasheet):
  - Interface: Standard USB Type B
  - Class: Printer (7) / Subclass: 1 / Protocol: 2 (bidirectional)
  - Endpoint: Bulk OUT for data transfer
"""

import asyncio
import logging
from typing import Optional

try:
    import usb.core
    import usb.util
    USB_AVAILABLE = True
except ImportError:
    USB_AVAILABLE = False

from app.core.printer import BasePrinter
from app.core.error_handler import PrinterError, PrinterErrorCode
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Printer status byte masks (from KP-300 datasheet — DLE EOT n command response)
STATUS_PAPER_OUT   = 0x20  # bit 5
STATUS_COVER_OPEN  = 0x04  # bit 2 (platen open)
STATUS_OVERHEAT    = 0x40  # bit 6 (head temperature)
STATUS_PAPER_JAM   = 0x08  # bit 3


class UsbPrinter(BasePrinter):
    """USB printer backend using pyusb."""

    def __init__(
        self,
        vendor_id: Optional[int] = None,
        product_id: Optional[int] = None,
    ):
        super().__init__()
        settings = get_settings()
        self._vendor_id = vendor_id or settings.usb_vendor_id
        self._product_id = product_id or settings.usb_product_id
        self._device = None
        self._endpoint_out = None

    def connection_type(self) -> str:
        return "usb"

    async def connect(self) -> None:
        """Find and claim USB device."""
        if not USB_AVAILABLE:
            # Simulation mode: no USB library present
            logger.warning("pyusb not available — running in USB simulation mode")
            self._mark_connected()
            return

        loop = asyncio.get_event_loop()
        try:
            device = await loop.run_in_executor(None, self._find_device)
            if device is None:
                raise PrinterError(
                    PrinterErrorCode.COMM_ERROR,
                    f"USB device {self._vendor_id:#06x}:{self._product_id:#06x} not found.",
                )
            await loop.run_in_executor(None, self._claim_device, device)
            self._device = device
            self._mark_connected()
            logger.info(f"USB printer connected ({self._vendor_id:#06x}:{self._product_id:#06x})")
        except PrinterError:
            raise
        except Exception as exc:
            raise PrinterError(PrinterErrorCode.COMM_ERROR, str(exc))

    def _find_device(self):
        return usb.core.find(idVendor=self._vendor_id, idProduct=self._product_id)

    def _claim_device(self, device) -> None:
        """Set active configuration and find bulk OUT endpoint."""
        if device.is_kernel_driver_active(0):
            device.detach_kernel_driver(0)
        device.set_configuration()
        cfg = device.get_active_configuration()
        intf = cfg[(0, 0)]
        self._endpoint_out = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress)
            == usb.util.ENDPOINT_OUT,
        )
        if self._endpoint_out is None:
            raise PrinterError(PrinterErrorCode.COMM_ERROR, "No USB bulk OUT endpoint found.")

    async def disconnect(self) -> None:
        if self._device is not None and USB_AVAILABLE:
            try:
                usb.util.dispose_resources(self._device)
            except Exception:
                pass
            self._device = None
        self._mark_disconnected()
        logger.info("USB printer disconnected.")

    async def write(self, data: bytes) -> None:
        if not self._connected:
            raise PrinterError(PrinterErrorCode.COMM_ERROR, "USB printer not connected.")

        if not USB_AVAILABLE or self._endpoint_out is None:
            # Simulation: log bytes count
            logger.debug(f"[USB SIM] Sent {len(data)} bytes to printer")
            return

        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, self._endpoint_out.write, data)
        except Exception as exc:
            self._mark_disconnected()
            self.schedule_reconnect()
            raise PrinterError(PrinterErrorCode.COMM_ERROR, str(exc))

    async def get_status(self) -> dict:
        """
        Query printer status via DLE EOT 1 (real-time status command).
        Falls back to simulated status if USB unavailable.
        """
        if not USB_AVAILABLE or self._device is None:
            return {
                "paper_ok": True,
                "cover_ok": True,
                "temperature_ok": True,
                "simulated": True,
            }

        # DLE EOT 1 — Transmit real-time status (printer status)
        DLE_EOT_CMD = b"\x10\x04\x01"
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, self._endpoint_out.write, DLE_EOT_CMD)
            # Read response
            endpoint_in = self._device[0][(0, 0)][0]
            raw = await loop.run_in_executor(None, endpoint_in.read, 1)
            status_byte = raw[0] if raw else 0
            return {
                "paper_ok":      not bool(status_byte & STATUS_PAPER_OUT),
                "cover_ok":      not bool(status_byte & STATUS_COVER_OPEN),
                "temperature_ok": not bool(status_byte & STATUS_OVERHEAT),
                "simulated": False,
            }
        except Exception as exc:
            logger.warning(f"Status query failed: {exc}")
            return {"paper_ok": None, "cover_ok": None, "temperature_ok": None, "simulated": False}
