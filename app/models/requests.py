"""
Request models for all API endpoints.
"""

from typing import Literal, Optional, Any
from pydantic import BaseModel, Field, field_validator
import base64


class ConnectRequest(BaseModel):
    connection_type: Literal["usb", "lan"] = Field(
        description="Connection interface: 'usb' or 'lan'"
    )
    # USB overrides
    usb_vendor_id: Optional[int] = Field(None, description="USB vendor ID (hex int)")
    usb_product_id: Optional[int] = Field(None, description="USB product ID (hex int)")
    # LAN overrides
    lan_host: Optional[str] = Field(None, description="Printer IP address")
    lan_port: Optional[int] = Field(None, ge=1, le=65535, description="Printer port")

    model_config = {"json_schema_extra": {
        "examples": [
            {"connection_type": "usb"},
            {"connection_type": "lan", "lan_host": "192.168.1.100", "lan_port": 9100},
        ]
    }}


class TextLine(BaseModel):
    text: str = Field(description="Line content")
    bold: bool = False
    underline: bool = False
    align: Literal["left", "center", "right"] = "left"
    font_size: Literal["normal", "double_height", "double_width", "double"] = "normal"


class PrintTextRequest(BaseModel):
    job_id: Optional[str] = Field(None, description="Client-supplied idempotency key")
    lines: list[TextLine] = Field(description="Lines to print")
    cut: bool = Field(True, description="Auto-cut after printing")
    language: Optional[str] = Field(None, description="Override language for error messages (e.g. 'tr')")

    model_config = {"json_schema_extra": {
        "examples": [{
            "job_id": "job-001",
            "lines": [
                {"text": "ACO RECYCLING", "bold": True, "align": "center", "font_size": "double"},
                {"text": "Reward: 3.00 TL", "bold": True, "align": "center"},
                {"text": "Glass: 0   Plastic: 2   Metal: 1", "align": "left"},
            ],
            "cut": True
        }]
    }}


class PrintImageRequest(BaseModel):
    job_id: Optional[str] = Field(None, description="Idempotency key")
    image_base64: str = Field(description="Base64-encoded PNG/JPEG image")
    align: Literal["left", "center", "right"] = "center"
    cut: bool = True
    language: Optional[str] = None

    @field_validator("image_base64")
    @classmethod
    def validate_base64(cls, v: str) -> str:
        try:
            base64.b64decode(v, validate=True)
        except Exception:
            raise ValueError("image_base64 must be valid base64-encoded data")
        return v


class PrintQRRequest(BaseModel):
    job_id: Optional[str] = Field(None)
    data: str = Field(description="Data to encode in QR code", min_length=1, max_length=2048)
    size: int = Field(6, ge=1, le=16, description="QR module size (1–16)")
    error_correction: Literal["L", "M", "Q", "H"] = "M"
    align: Literal["left", "center", "right"] = "center"
    label: Optional[str] = Field(None, description="Optional text label printed below QR")
    cut: bool = True
    language: Optional[str] = None


class SmartPrintRequest(BaseModel):
    """Optional bonus: LLM-assisted receipt generation from structured data."""
    job_id: Optional[str] = Field(None)
    data: dict[str, Any] = Field(description="Structured data to convert to receipt")
    template_hint: Optional[str] = Field(None, description="Hint for LLM about receipt type")
    language: Optional[str] = Field(None, description="Output language for receipt content")
    cut: bool = True


class ReprintRequest(BaseModel):
    job_id: str = Field(description="Job ID to reprint")
    language: Optional[str] = None
