"""
Yazıcı hata simülasyon endpoint'leri.

Bu endpoint'ler test ve demo amaçlı yazıcı hatalarını simüle eder.
Gerçek üretim ortamında devre dışı bırakılabilir.
"""

from typing import Optional, Literal
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import verify_token
from app.core.printer import get_printer
from app.core.error_handler import PrinterErrorCode
from tests.mock_printer import MockPrinter

router = APIRouter(tags=["Simülasyon"])


class SimulateRequest(BaseModel):
    """Hata simülasyon isteği"""
    error_type: Optional[Literal[
        "PAPER_OUT",
        "PAPER_JAM", 
        "COVER_OPEN",
        "OVERHEAT",
        "COMM_ERROR",
        "UNKNOWN_COMMAND"
    ]] = Field(
        None,
        description="Simüle edilecek hata tipi. null = hataları temizle"
    )
    operations: int = Field(
        -1,
        description="Kaç operasyon için hata simüle edilecek. -1 = sürekli, N = N operasyon"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error_type": "PAPER_OUT",
                    "operations": -1
                },
                {
                    "error_type": "PAPER_JAM",
                    "operations": 3
                },
                {
                    "error_type": None,
                    "operations": 0
                }
            ]
        }
    }


class SimulateResponse(BaseModel):
    """Hata simülasyon yanıtı"""
    status: Literal["activated", "cleared", "error"] = Field(
        description="Simülasyon durumu"
    )
    message: str = Field(description="Durum mesajı")
    error_type: Optional[str] = Field(None, description="Aktif hata tipi")
    operations: Optional[int] = Field(None, description="Kalan operasyon sayısı")
    timestamp: datetime = Field(description="İşlem zamanı (UTC)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "activated",
                    "message": "PAPER_OUT hatası aktive edildi",
                    "error_type": "PAPER_OUT",
                    "operations": -1,
                    "timestamp": "2026-05-27T00:00:00Z"
                }
            ]
        }
    }


class SimulateStatusResponse(BaseModel):
    """Simülasyon durum yanıtı"""
    simulation_active: bool = Field(description="Simülasyon aktif mi?")
    current_error: Optional[str] = Field(None, description="Aktif hata tipi")
    operations_remaining: Optional[int] = Field(
        None,
        description="Kalan operasyon sayısı (-1 = sürekli)"
    )
    is_mock_printer: bool = Field(description="Mock printer kullanılıyor mu?")
    timestamp: datetime = Field(description="Sorgu zamanı (UTC)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "simulation_active": True,
                    "current_error": "PAPER_OUT",
                    "operations_remaining": -1,
                    "is_mock_printer": True,
                    "timestamp": "2026-05-27T00:00:00Z"
                }
            ]
        }
    }


@router.post(
    "/simulate",
    response_model=SimulateResponse,
    dependencies=[Depends(verify_token)],
    summary="Yazıcı Hatası Simüle Et",
    description="""
Yazıcı donanım hatalarını simüle eder (sadece MockPrinter ile çalışır).

## Kullanım

### Hata Aktive Etme
```json
{
  "error_type": "PAPER_OUT",
  "operations": -1
}
```

### Geçici Hata (3 operasyon için)
```json
{
  "error_type": "PAPER_JAM",
  "operations": 3
}
```

### Hataları Temizleme
```json
{
  "error_type": null,
  "operations": 0
}
```

## Hata Tipleri

- **PAPER_OUT**: Kağıt bitti
- **PAPER_JAM**: Kağıt sıkıştı
- **COVER_OPEN**: Kapak açık
- **OVERHEAT**: Aşırı ısınma
- **COMM_ERROR**: İletişim hatası
- **UNKNOWN_COMMAND**: Bilinmeyen komut

## Notlar

⚠️ Bu endpoint sadece test ve demo amaçlıdır.
⚠️ Sadece MockPrinter ile çalışır (gerçek yazıcıda çalışmaz).
⚠️ Üretim ortamında devre dışı bırakılmalıdır.
    """,
    response_description="Simülasyon durumu",
    responses={
        200: {
            "description": "Simülasyon başarıyla yapılandırıldı"
        },
        400: {
            "description": "Geçersiz istek veya MockPrinter kullanılmıyor"
        },
        502: {
            "description": "Yazıcı bağlı değil"
        }
    }
)
async def simulate_error(request: SimulateRequest):
    """Yazıcı hatası simüle et"""
    printer = get_printer()
    
    # Yazıcı kontrolü
    if printer is None or not printer.connected:
        raise HTTPException(
            status_code=502,
            detail={
                "error": {
                    "code": "COMM_ERROR",
                    "detail": "Yazıcı bağlı değil. Önce yazıcıya bağlanın."
                }
            }
        )
    
    # MockPrinter kontrolü
    if not isinstance(printer, MockPrinter):
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_OPERATION",
                    "detail": "Simülasyon sadece MockPrinter ile çalışır. Gerçek yazıcıda kullanılamaz."
                }
            }
        )
    
    # Hataları temizle
    if request.error_type is None:
        printer.clear_errors()
        return SimulateResponse(
            status="cleared",
            message="Tüm simülasyon hataları temizlendi",
            error_type=None,
            operations=None,
            timestamp=datetime.now(timezone.utc)
        )
    
    # Hatayı simüle et
    printer.simulate_error(request.error_type, operations=request.operations)
    
    return SimulateResponse(
        status="activated",
        message=f"{request.error_type} hatası aktive edildi",
        error_type=request.error_type,
        operations=request.operations,
        timestamp=datetime.now(timezone.utc)
    )


@router.get(
    "/simulate/status",
    response_model=SimulateStatusResponse,
    dependencies=[Depends(verify_token)],
    summary="Simülasyon Durumunu Sorgula",
    description="""
Aktif simülasyon durumunu sorgular.

## Yanıt

- **simulation_active**: Bir hata simülasyonu aktif mi?
- **current_error**: Aktif hata tipi (varsa)
- **operations_remaining**: Kalan operasyon sayısı (-1 = sürekli)
- **is_mock_printer**: MockPrinter kullanılıyor mu?

## Kullanım Senaryoları

- Test öncesi simülasyon durumunu kontrol etme
- Test sonrası simülasyonun temizlendiğini doğrulama
- Debugging ve troubleshooting
    """,
    response_description="Simülasyon durum bilgisi"
)
async def get_simulate_status():
    """Simülasyon durumunu sorgula"""
    printer = get_printer()
    
    # Yazıcı bağlı değilse
    if printer is None or not printer.connected:
        return SimulateStatusResponse(
            simulation_active=False,
            current_error=None,
            operations_remaining=None,
            is_mock_printer=False,
            timestamp=datetime.now(timezone.utc)
        )
    
    # MockPrinter kontrolü
    is_mock = isinstance(printer, MockPrinter)
    
    if not is_mock:
        return SimulateStatusResponse(
            simulation_active=False,
            current_error=None,
            operations_remaining=None,
            is_mock_printer=False,
            timestamp=datetime.now(timezone.utc)
        )
    
    # MockPrinter durumunu al
    simulation_active = printer._error_code is not None
    current_error = printer._error_code.value if printer._error_code else None
    operations_remaining = printer._error_operations_remaining if simulation_active else None
    
    return SimulateStatusResponse(
        simulation_active=simulation_active,
        current_error=current_error,
        operations_remaining=operations_remaining,
        is_mock_printer=True,
        timestamp=datetime.now(timezone.utc)
    )
