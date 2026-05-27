"""
Response models for all API endpoints.
"""

from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Hata detay bilgisi"""
    code: str = Field(description="Hata kodu (PAPER_OUT, COMM_ERROR, vb.)")
    detail: str = Field(description="Hata açıklaması")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": "PAPER_OUT",
                    "detail": "Kağıt bitti. Lütfen kağıt yükleyin ve tekrar deneyin."
                }
            ]
        }
    }


class JobResponse(BaseModel):
    """Yazdırma işi yanıtı"""
    job_id: str = Field(description="İş kimliği")
    status: Literal["queued", "printing", "done", "failed"] = Field(description="İş durumu")
    message: str = Field(description="Durum mesajı")
    timestamp: datetime = Field(description="İşlem zamanı (UTC)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "job_id": "receipt-001",
                    "status": "done",
                    "message": "Yazdırma işlemi başarıyla tamamlandı",
                    "timestamp": "2026-05-27T00:00:00Z"
                }
            ]
        }
    }


class ConnectResponse(BaseModel):
    """Bağlantı işlemi yanıtı"""
    status: Literal["connected", "disconnected", "error"] = Field(description="Bağlantı durumu")
    connection_type: Optional[Literal["usb", "lan"]] = Field(None, description="Bağlantı tipi")
    message: str = Field(description="Durum mesajı")
    timestamp: datetime = Field(description="İşlem zamanı (UTC)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "connected",
                    "connection_type": "usb",
                    "message": "Yazıcıya başarıyla bağlanıldı",
                    "timestamp": "2026-05-27T00:00:00Z"
                },
                {
                    "status": "connected",
                    "connection_type": "lan",
                    "message": "Yazıcıya başarıyla bağlanıldı",
                    "timestamp": "2026-05-27T00:00:00Z"
                }
            ]
        }
    }


class StatusResponse(BaseModel):
    """Yazıcı durum bilgisi"""
    connected: bool = Field(description="Yazıcı bağlı mı?")
    connection_type: Optional[Literal["usb", "lan"]] = Field(None, description="Bağlantı tipi")
    printer_model: str = Field("Cashino KP-300/KP-301H", description="Yazıcı modeli")
    paper_ok: Optional[bool] = Field(None, description="Kağıt durumu (True: OK, False: Bitti)")
    cover_ok: Optional[bool] = Field(None, description="Kapak durumu (True: Kapalı, False: Açık)")
    temperature_ok: Optional[bool] = Field(None, description="Sıcaklık durumu (True: Normal, False: Aşırı ısınma)")
    error_code: Optional[str] = Field(None, description="Aktif hata kodu (PAPER_OUT, PAPER_JAM, vb.)")
    active_job_id: Optional[str] = Field(None, description="Aktif iş kimliği")
    queue_size: int = Field(0, description="Kuyruktaki iş sayısı")
    uptime_seconds: float = Field(0.0, description="Yazıcı çalışma süresi (saniye)")
    timestamp: datetime = Field(description="Sorgu zamanı (UTC)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "connected": True,
                    "connection_type": "usb",
                    "printer_model": "Cashino KP-300/KP-301H",
                    "paper_ok": True,
                    "cover_ok": True,
                    "temperature_ok": True,
                    "active_job_id": None,
                    "queue_size": 0,
                    "uptime_seconds": 3600.5,
                    "timestamp": "2026-05-27T00:00:00Z"
                }
            ]
        }
    }


class LogEntry(BaseModel):
    """Log kaydı"""
    ts: str = Field(description="Zaman damgası (ISO-8601)")
    op: str = Field(description="İşlem adı (print_text, connect, vb.)")
    conn: Optional[str] = Field(None, description="Bağlantı tipi (usb/lan)")
    job_id: Optional[str] = Field(None, description="İş kimliği")
    status: str = Field(description="Durum (done/failed/info)")
    error: Optional[ErrorDetail] = Field(None, description="Hata detayı (varsa)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "ts": "2026-05-27T00:00:00Z",
                    "op": "print_text",
                    "conn": "usb",
                    "job_id": "receipt-001",
                    "status": "done",
                    "error": None
                }
            ]
        }
    }


class LogsResponse(BaseModel):
    """Log listesi yanıtı"""
    total: int = Field(description="Toplam log sayısı")
    entries: list[LogEntry] = Field(description="Log kayıtları")
    page: int = Field(1, description="Mevcut sayfa")
    page_size: int = Field(100, description="Sayfa başına kayıt")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total": 150,
                    "entries": [
                        {
                            "ts": "2026-05-27T00:00:00Z",
                            "op": "print_text",
                            "conn": "usb",
                            "job_id": "receipt-001",
                            "status": "done",
                            "error": None
                        }
                    ],
                    "page": 1,
                    "page_size": 100
                }
            ]
        }
    }


class PaperStatsResponse(BaseModel):
    """Rulo kağıt kullanım tahmini"""
    total_roll_mm: float = Field(description="Toplam rulo uzunluğu (mm)")
    used_mm: float = Field(description="Tahmini kullanılan uzunluk (mm)")
    remaining_mm: float = Field(description="Tahmini kalan uzunluk (mm)")
    remaining_m: float = Field(description="Tahmini kalan uzunluk (m)")
    remaining_pct: float = Field(description="Tahmini kalan yüzde (%)")
    print_count: int = Field(description="Bu rulodaki toplam baskı sayısı")
    avg_mm_per_print: float = Field(description="Baskı başına ortalama kağıt (mm)")
    prints_remaining: int = Field(description="Tahmini kalan baskı sayısı")
    last_reset: Optional[str] = Field(None, description="Son rulo değişim zamanı")
    last_print: Optional[str] = Field(None, description="Son baskı zamanı")


class HealthResponse(BaseModel):
    """Servis sağlık durumu"""
    status: Literal["ok", "degraded"] = Field(description="Servis durumu")
    version: str = Field(description="Servis versiyonu")
    uptime_seconds: float = Field(description="Servis çalışma süresi (saniye)")
    printer_connected: bool = Field(description="Yazıcı bağlı mı?")
    queue_size: int = Field(description="Kuyruktaki iş sayısı")
    memory_mb: float = Field(description="Bellek kullanımı (MB)")
    paper_remaining_pct: Optional[float] = Field(None, description="Tahmini rulo kalan yüzdesi")
    paper_prints_remaining: Optional[int] = Field(None, description="Tahmini kalan baskı sayısı")
    timestamp: datetime = Field(description="Sorgu zamanı (UTC)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "ok",
                    "version": "1.0.0",
                    "uptime_seconds": 7200.5,
                    "printer_connected": True,
                    "queue_size": 0,
                    "memory_mb": 45.23,
                    "timestamp": "2026-05-27T00:00:00Z"
                }
            ]
        }
    }
