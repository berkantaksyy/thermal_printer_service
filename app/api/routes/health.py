"""
Servis sağlık kontrolü endpoint'i
"""

import time
from datetime import datetime, timezone
from fastapi import APIRouter

try:
    import psutil
    _PSUTIL_AVAILABLE = True
except ImportError:
    _PSUTIL_AVAILABLE = False

from app.core.config import get_settings
from app.core.printer import get_printer
from app.models.responses import HealthResponse
from app.services.queue_service import get_queue_service

router = APIRouter(tags=["💚 Sağlık"])

_start_time = time.monotonic()


@router.get("/health", response_model=HealthResponse)
async def health():
    """
    Servis sağlık kontrolü (Docker/Kubernetes için).
    
    **Özellik:** Bearer token gerektirmez.
    
    **Dönen Bilgiler:**
    - Servis durumu (ok/degraded)
    - Versiyon
    - Çalışma süresi
    - Yazıcı bağlantı durumu
    - Kuyruk boyutu
    - Bellek kullanımı
    """
    settings = get_settings()
    printer = get_printer()
    queue = get_queue_service()
    connected = printer is not None and printer.connected

    try:
        mem_mb = psutil.Process().memory_info().rss / (1024 * 1024) if _PSUTIL_AVAILABLE else 0.0
    except Exception:
        mem_mb = 0.0

    return HealthResponse(
        status="ok" if connected else "degraded",
        version=settings.app_version,
        uptime_seconds=time.monotonic() - _start_time,
        printer_connected=connected,
        queue_size=queue.queue_size(),
        memory_mb=round(mem_mb, 2),
        timestamp=datetime.now(timezone.utc),
    )
