"""
Yazıcı durum endpoint'i
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends

from app.api.deps import verify_token
from app.core.printer import get_printer
from app.models.responses import StatusResponse
from app.services.queue_service import get_queue_service

router = APIRouter(tags=["📊 Durum"])


@router.get("/status", response_model=StatusResponse, dependencies=[Depends(verify_token)])
async def get_status():
    """
    Yazıcı durumunu sorgula.
    
    **Dönen Bilgiler:**
    - Bağlantı durumu (bağlı/bağlı değil)
    - Bağlantı tipi (USB/LAN)
    - Kağıt durumu
    - Kapak durumu
    - Sıcaklık durumu
    - Kuyruk boyutu
    - Çalışma süresi
    """
    printer = get_printer()
    queue = get_queue_service()

    if printer is None or not printer.connected:
        return StatusResponse(
            connected=False,
            queue_size=queue.queue_size(),
            timestamp=datetime.now(timezone.utc),
        )

    hw_status = await printer.get_status()
    return StatusResponse(
        connected=True,
        connection_type=printer.connection_type(),
        paper_ok=hw_status.get("paper_ok"),
        cover_ok=hw_status.get("cover_ok"),
        temperature_ok=hw_status.get("temperature_ok"),
        queue_size=queue.queue_size(),
        uptime_seconds=printer.uptime_seconds,
        timestamp=datetime.now(timezone.utc),
    )
