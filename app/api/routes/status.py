"""
Yazıcı durum endpoint'i
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends

from app.api.deps import verify_token
from app.core.printer import get_printer
from app.models.responses import StatusResponse
from app.services.queue_service import get_queue_service

router = APIRouter(tags=["Durum"])


@router.get(
    "/status",
    response_model=StatusResponse,
    dependencies=[Depends(verify_token)],
    summary="Yazıcı Durumunu Sorgula",
    description="""
Yazıcının anlık durumunu ve sistem bilgilerini döner.

## Dönen Bilgiler

### Bağlantı Bilgileri
- **connected**: Yazıcı bağlı mı?
- **connection_type**: Bağlantı tipi (USB veya LAN)
- **printer_model**: Yazıcı model bilgisi

### Donanım Durumu
- **paper_ok**: Kağıt durumu (true: var, false: bitti, null: bilinmiyor)
- **cover_ok**: Kapak durumu (true: kapalı, false: açık, null: bilinmiyor)
- **temperature_ok**: Sıcaklık durumu (true: normal, false: aşırı ısınma, null: bilinmiyor)

### Sistem Bilgileri
- **queue_size**: Kuyruktaki bekleyen iş sayısı
- **uptime_seconds**: Yazıcı bağlantısının çalışma süresi (saniye)
- **active_job_id**: Şu anda işlenen iş kimliği (varsa)

## Kullanım Senaryoları
- Periyodik sağlık kontrolü (health check)
- Yazdırma öncesi durum kontrolü
- Hata durumu tespiti
- Monitoring ve alerting sistemleri için veri kaynağı

## Önerilen Polling Süresi
- Normal kullanım: 10-30 saniye
- Aktif yazdırma sırasında: 2-5 saniye
- Hata durumunda: 1-2 saniye
    """,
    response_description="Yazıcı durum bilgileri",
    responses={
        200: {
            "description": "Durum bilgileri başarıyla alındı",
            "content": {
                "application/json": {
                    "examples": {
                        "connected": {
                            "summary": "Bağlı ve Hazır",
                            "value": {
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
                        },
                        "paper_out": {
                            "summary": "Kağıt Bitti",
                            "value": {
                                "connected": True,
                                "connection_type": "usb",
                                "printer_model": "Cashino KP-300/KP-301H",
                                "paper_ok": False,
                                "cover_ok": True,
                                "temperature_ok": True,
                                "active_job_id": None,
                                "queue_size": 2,
                                "uptime_seconds": 3600.5,
                                "timestamp": "2026-05-27T00:00:00Z"
                            }
                        },
                        "disconnected": {
                            "summary": "Bağlı Değil",
                            "value": {
                                "connected": False,
                                "connection_type": None,
                                "printer_model": "Cashino KP-300/KP-301H",
                                "paper_ok": None,
                                "cover_ok": None,
                                "temperature_ok": None,
                                "active_job_id": None,
                                "queue_size": 0,
                                "uptime_seconds": 0.0,
                                "timestamp": "2026-05-27T00:00:00Z"
                            }
                        }
                    }
                }
            }
        }
    }
)
async def get_status():
    """Yazıcı durumunu sorgula"""
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
