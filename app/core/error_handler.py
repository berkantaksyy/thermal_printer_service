"""
Printer error codes and structured error handling.

Error codes match the task specification exactly:
  PAPER_OUT, PAPER_JAM, COVER_OPEN, OVERHEAT, COMM_ERROR, UNKNOWN_COMMAND

Each code maps to:
  - KP-300/KP-301H LED flash count (from datasheets)
  - HTTP status code
  - Default English message (i18n key also provided)
"""

from enum import Enum
from fastapi import HTTPException


class PrinterErrorCode(str, Enum):
    PAPER_OUT = "PAPER_OUT"
    PAPER_JAM = "PAPER_JAM"
    COVER_OPEN = "COVER_OPEN"
    OVERHEAT = "OVERHEAT"
    COMM_ERROR = "COMM_ERROR"
    UNKNOWN_COMMAND = "UNKNOWN_COMMAND"


# Maps error code → (LED flash count per datasheet, i18n key, HTTP status)
ERROR_METADATA: dict[PrinterErrorCode, tuple[int, str, int]] = {
    PrinterErrorCode.PAPER_OUT:       (3, "error.paper_out",       503),
    PrinterErrorCode.PAPER_JAM:       (4, "error.paper_jam",       503),
    PrinterErrorCode.COVER_OPEN:      (6, "error.cover_open",      503),
    PrinterErrorCode.OVERHEAT:        (5, "error.overheat",        503),
    PrinterErrorCode.COMM_ERROR:      (0, "error.comm_error",      502),
    PrinterErrorCode.UNKNOWN_COMMAND: (0, "error.unknown_command", 400),
}

# Default English messages (used when i18n service is unavailable)
_DEFAULT_MESSAGES: dict[PrinterErrorCode, str] = {
    PrinterErrorCode.PAPER_OUT:       "Paper is out. Please load paper and retry.",
    PrinterErrorCode.PAPER_JAM:       "Paper jam detected. Clear the jam and retry.",
    PrinterErrorCode.COVER_OPEN:      "Printer cover is open. Close it and retry.",
    PrinterErrorCode.OVERHEAT:        "Printer is overheating. Wait for it to cool down.",
    PrinterErrorCode.COMM_ERROR:      "Communication error with the printer.",
    PrinterErrorCode.UNKNOWN_COMMAND: "Unknown or unsupported ESC/POS command.",
}


class PrinterError(Exception):
    """Raised when a printer operation fails with a known error code."""

    def __init__(
        self,
        code: PrinterErrorCode,
        detail: str | None = None,
        job_id: str | None = None,
    ):
        self.code = code
        self.detail = detail or _DEFAULT_MESSAGES[code]
        self.job_id = job_id
        super().__init__(self.detail)

    @property
    def http_status(self) -> int:
        return ERROR_METADATA[self.code][2]

    @property
    def i18n_key(self) -> str:
        return ERROR_METADATA[self.code][1]

    @property
    def led_flashes(self) -> int:
        return ERROR_METADATA[self.code][0]

    def to_dict(self) -> dict:
        return {"code": self.code.value, "detail": self.detail}


def printer_error_to_http(err: PrinterError) -> HTTPException:
    """Convert a PrinterError to FastAPI HTTPException."""
    return HTTPException(
        status_code=err.http_status,
        detail={"error": err.to_dict(), "job_id": err.job_id},
    )
