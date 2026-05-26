"""
Response models for all API endpoints.
"""

from typing import Optional, Any, Literal
from datetime import datetime
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    detail: str


class JobResponse(BaseModel):
    job_id: str
    status: Literal["queued", "printing", "done", "failed"]
    message: str
    timestamp: datetime


class ConnectResponse(BaseModel):
    status: Literal["connected", "disconnected", "error"]
    connection_type: Optional[Literal["usb", "lan"]] = None
    message: str
    timestamp: datetime


class StatusResponse(BaseModel):
    connected: bool
    connection_type: Optional[Literal["usb", "lan"]] = None
    printer_model: str = "Cashino KP-300/KP-301H"
    paper_ok: Optional[bool] = None
    cover_ok: Optional[bool] = None
    temperature_ok: Optional[bool] = None
    active_job_id: Optional[str] = None
    queue_size: int = 0
    uptime_seconds: float = 0.0
    timestamp: datetime


class LogEntry(BaseModel):
    ts: str                           # ISO-8601
    op: str                           # operation name
    conn: Optional[str] = None       # usb | lan | None
    job_id: Optional[str] = None
    status: str                       # done | failed | info
    error: Optional[ErrorDetail] = None


class LogsResponse(BaseModel):
    total: int
    entries: list[LogEntry]
    page: int = 1
    page_size: int = 100


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    uptime_seconds: float
    printer_connected: bool
    queue_size: int
    memory_mb: float
    timestamp: datetime
