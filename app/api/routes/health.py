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
from app.services.paper_service import get_paper_service

router = APIRouter(tags=["Sağlık"])

_start_time = time.monotonic()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Servis Sağlık Kontrolü",
    description="""
Servisin genel sağlık durumunu döner. Docker, Kubernetes ve diğer orkestrasyon araçları için health check endpoint'i olarak kullanılabilir.

## Özellikler
- **Kimlik Doğrulama Gerektirmez**: Bearer token olmadan erişilebilir
- **Hızlı Yanıt**: Minimum gecikme ile durum bilgisi
- **Detaylı Metrikler**: Bellek, uptime, kuyruk boyutu

## Dönen Bilgiler

### Servis Durumu
- **status**:
  - `ok`: Yazıcı bağlı ve çalışıyor
  - `degraded`: Yazıcı bağlı değil ama servis çalışıyor

### Sistem Metrikleri
- **version**: Servis versiyonu
- **uptime_seconds**: Servisin çalışma süresi (saniye)
- **memory_mb**: Bellek kullanımı (MB)

### Yazıcı Bilgileri
- **printer_connected**: Yazıcı bağlantı durumu
- **queue_size**: Kuyruktaki bekleyen iş sayısı

## Kullanım Senaryoları

### Docker Health Check
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8000/health || exit 1
```

### Kubernetes Liveness Probe
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 30
```

### Monitoring Sistemleri
Prometheus, Grafana, Datadog gibi monitoring araçları için veri kaynağı olarak kullanılabilir.
    """,
    response_description="Servis sağlık durumu",
    responses={
        200: {
            "description": "Sağlık durumu başarıyla alındı",
            "content": {
                "application/json": {
                    "examples": {
                        "healthy": {
                            "summary": "Sağlıklı (Yazıcı Bağlı)",
                            "value": {
                                "status": "ok",
                                "version": "1.0.0",
                                "uptime_seconds": 7200.5,
                                "printer_connected": True,
                                "queue_size": 0,
                                "memory_mb": 45.23,
                                "timestamp": "2026-05-27T00:00:00Z"
                            }
                        },
                        "degraded": {
                            "summary": "Düşük Performans (Yazıcı Bağlı Değil)",
                            "value": {
                                "status": "degraded",
                                "version": "1.0.0",
                                "uptime_seconds": 7200.5,
                                "printer_connected": False,
                                "queue_size": 3,
                                "memory_mb": 45.23,
                                "timestamp": "2026-05-27T00:00:00Z"
                            }
                        }
                    }
                }
            }
        }
    }
)
async def health():
    """Servis sağlık kontrolü"""
    settings = get_settings()
    printer = get_printer()
    queue = get_queue_service()
    connected = printer is not None and printer.connected

    try:
        mem_mb = psutil.Process().memory_info().rss / (1024 * 1024) if _PSUTIL_AVAILABLE else 0.0
    except Exception:
        mem_mb = 0.0

    paper = get_paper_service().get_stats()
    return HealthResponse(
        status="ok" if connected else "degraded",
        version=settings.app_version,
        uptime_seconds=time.monotonic() - _start_time,
        printer_connected=connected,
        queue_size=queue.queue_size(),
        memory_mb=round(mem_mb, 2),
        paper_remaining_pct=paper["remaining_pct"],
        paper_prints_remaining=paper["prints_remaining"],
        timestamp=datetime.now(timezone.utc),
    )
