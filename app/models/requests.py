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
    """Metin satırı formatı"""
    text: str = Field(description="Satır içeriği")
    bold: bool = Field(False, description="Kalın yazı")
    underline: bool = Field(False, description="Altı çizili")
    align: Literal["left", "center", "right"] = Field("left", description="Hizalama")
    font_size: Literal["normal", "double_height", "double_width", "double"] = Field("normal", description="Font boyutu")


class PrintTextRequest(BaseModel):
    """Metin yazdırma isteği"""
    job_id: Optional[str] = Field(None, description="İş kimliği (idempotency için)")
    lines: list[TextLine] = Field(description="Yazdırılacak satırlar")
    cut: bool = Field(True, description="Yazdırma sonrası otomatik kağıt kesme")
    language: Optional[str] = Field(None, description="Dil kodu (tr/en/de/fr)")

    model_config = {"json_schema_extra": {
        "examples": [{
            "job_id": "receipt-001",
            "lines": [
                {"text": "ACO RECYCLING", "bold": True, "align": "center", "font_size": "double"},
                {"text": "Ödül: 3.00 TL", "bold": True, "align": "center"},
                {"text": "Cam: 0   Plastik: 2   Metal: 1", "align": "left"},
            ],
            "cut": True,
            "language": "tr"
        }]
    }}


class PrintImageRequest(BaseModel):
    """Görsel yazdırma isteği"""
    job_id: Optional[str] = Field(None, description="İş kimliği")
    image_base64: str = Field(description="Base64 kodlanmış PNG/JPEG görsel")
    align: Literal["left", "center", "right"] = Field("center", description="Hizalama")
    cut: bool = Field(True, description="Otomatik kağıt kesme")
    language: Optional[str] = Field(None, description="Dil kodu")

    model_config = {"json_schema_extra": {
        "examples": [{
            "job_id": "image-001",
            "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "align": "center",
            "cut": True
        }]
    }}

    @field_validator("image_base64")
    @classmethod
    def validate_base64(cls, v: str) -> str:
        try:
            base64.b64decode(v, validate=True)
        except Exception:
            raise ValueError("image_base64 geçerli base64 verisi olmalıdır")
        return v


class PrintQRRequest(BaseModel):
    """QR kod yazdırma isteği"""
    job_id: Optional[str] = Field(None, description="İş kimliği")
    data: str = Field(description="QR kodda saklanacak veri", min_length=1, max_length=2048)
    size: int = Field(6, ge=1, le=16, description="QR modül boyutu (1-16)")
    error_correction: Literal["L", "M", "Q", "H"] = Field("M", description="Hata düzeltme seviyesi")
    align: Literal["left", "center", "right"] = Field("center", description="Hizalama")
    label: Optional[str] = Field(None, description="QR kod altında gösterilecek etiket")
    cut: bool = Field(True, description="Otomatik kağıt kesme")
    language: Optional[str] = Field(None, description="Dil kodu")

    model_config = {"json_schema_extra": {
        "examples": [{
            "job_id": "qr-001",
            "data": "https://example.com/receipt/12345",
            "size": 6,
            "error_correction": "M",
            "align": "center",
            "label": "Detaylar için tarayın",
            "cut": True
        }]
    }}


class SmartPrintRequest(BaseModel):
    """Yapay zeka destekli akıllı yazdırma isteği"""
    job_id: Optional[str] = Field(None, description="İş kimliği")
    data: dict[str, Any] = Field(description="Fiş formatına dönüştürülecek yapılandırılmış veri")
    template_hint: Optional[str] = Field(None, description="Fiş tipi ipucu (örn: 'kafe fişi', 'geri dönüşüm makbuzu')")
    language: Optional[str] = Field(None, description="Çıktı dili (tr/en/de/fr)")
    cut: bool = Field(True, description="Otomatik kağıt kesme")

    model_config = {"json_schema_extra": {
        "examples": [{
            "job_id": "smart-001",
            "data": {
                "machine_id": "ACO-TEST-0001",
                "reward": "3.00 TL",
                "plastic": 2,
                "metal": 1,
                "glass": 0
            },
            "template_hint": "geri dönüşüm ödül fişi",
            "language": "tr",
            "cut": True
        }]
    }}


class ReprintRequest(BaseModel):
    """Yeniden yazdırma isteği"""
    job_id: str = Field(description="Yeniden yazdırılacak iş kimliği")
    language: Optional[str] = Field(None, description="Dil kodu")

    model_config = {"json_schema_extra": {
        "examples": [{
            "job_id": "receipt-001",
            "language": "tr"
        }]
    }}
