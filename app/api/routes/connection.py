"""
Yazıcı bağlantı endpoint'leri
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends

from app.api.deps import verify_token
from app.core.printer import PrinterFactory, get_printer, set_printer
from app.core.error_handler import PrinterError, printer_error_to_http
from app.models.requests import ConnectRequest
from app.models.responses import ConnectResponse
from app.services.log_service import get_log_service
from app.services.i18n_service import get_i18n_service

router = APIRouter(prefix="/connect", tags=["Bağlantı"])


@router.post(
    "",
    response_model=ConnectResponse,
    dependencies=[Depends(verify_token)],
    summary="Yazıcıya Bağlan",
    description="""
Termal yazıcıya USB veya LAN üzerinden bağlantı kurar.

## Bağlantı Tipleri

### USB Bağlantısı
Yazıcı USB kablosu ile bilgisayara bağlıysa bu yöntemi kullanın.
- Vendor ID ve Product ID otomatik algılanır
- Özel değerler belirtmek isterseniz `usb_vendor_id` ve `usb_product_id` parametrelerini kullanabilirsiniz

### LAN Bağlantısı
Yazıcı ağa bağlıysa IP adresi ve port ile bağlanın.
- Varsayılan port: 9100 (RAW printing standardı)
- Yazıcının IP adresini yazıcı ayarlarından veya ağ taraması ile bulabilirsiniz

## Özellikler
- Mevcut bağlantı varsa otomatik olarak kesilir
- Bağlantı başarısız olursa otomatik yeniden deneme mekanizması devreye girer
- Tüm bağlantı işlemleri loglanır

## Hata Durumları
- **503 Service Unavailable**: Yazıcı bulunamadı veya bağlantı kurulamadı
- **400 Bad Request**: Geçersiz parametreler
    """,
    response_description="Bağlantı başarıyla kuruldu",
    responses={
        200: {
            "description": "Yazıcıya başarıyla bağlanıldı",
            "content": {
                "application/json": {
                    "examples": {
                        "usb": {
                            "summary": "USB Bağlantısı",
                            "value": {
                                "status": "connected",
                                "connection_type": "usb",
                                "message": "Yazıcıya başarıyla bağlanıldı",
                                "timestamp": "2026-05-27T00:00:00Z"
                            }
                        },
                        "lan": {
                            "summary": "LAN Bağlantısı",
                            "value": {
                                "status": "connected",
                                "connection_type": "lan",
                                "message": "Yazıcıya başarıyla bağlanıldı",
                                "timestamp": "2026-05-27T00:00:00Z"
                            }
                        }
                    }
                }
            }
        },
        503: {
            "description": "Yazıcıya bağlanılamadı",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "error": {
                                "code": "COMM_ERROR",
                                "detail": "Yazıcı bulunamadı. USB bağlantısını kontrol edin."
                            }
                        }
                    }
                }
            }
        }
    }
)
async def connect(req: ConnectRequest):
    """Yazıcıya bağlan"""
    log = get_log_service()
    i18n = get_i18n_service()

    # Disconnect existing
    existing = get_printer()
    if existing and existing.connected:
        await existing.disconnect()

    kwargs: dict = {}
    if req.connection_type == "usb":
        if req.usb_vendor_id:
            kwargs["vendor_id"] = req.usb_vendor_id
        if req.usb_product_id:
            kwargs["product_id"] = req.usb_product_id
    else:
        if req.lan_host:
            kwargs["host"] = req.lan_host
        if req.lan_port:
            kwargs["port"] = req.lan_port

    printer = PrinterFactory.create(req.connection_type, **kwargs)
    try:
        await printer.connect()
        set_printer(printer)
        await log.log(op="connect", status="done", conn=req.connection_type)
        return ConnectResponse(
            status="connected",
            connection_type=req.connection_type,
            message=i18n.t("status.connected"),
            timestamp=datetime.now(timezone.utc),
        )
    except PrinterError as err:
        await log.log(
            op="connect", status="failed",
            conn=req.connection_type,
            error_code=err.code.value,
            error_detail=err.detail,
        )
        raise printer_error_to_http(err)


@router.post(
    "/disconnect",
    response_model=ConnectResponse,
    dependencies=[Depends(verify_token)],
    summary="Bağlantıyı Kes",
    description="""
Yazıcı ile olan aktif bağlantıyı güvenli bir şekilde sonlandırır.

## Ne Zaman Kullanılır?
- Yazıcıyı başka bir uygulama kullanacaksa
- Servis kapatılmadan önce temiz bir şekilde bağlantıyı kesmek için
- Bağlantı tipini değiştirmek için (USB'den LAN'a veya tersi)

## Özellikler
- Aktif yazdırma işi varsa tamamlanmasını bekler
- Bağlantı yoksa hata vermez, başarılı yanıt döner
- Tüm işlemler loglanır
    """,
    response_description="Bağlantı başarıyla kesildi",
    responses={
        200: {
            "description": "Bağlantı kesildi",
            "content": {
                "application/json": {
                    "example": {
                        "status": "disconnected",
                        "connection_type": None,
                        "message": "Bağlantı kesildi",
                        "timestamp": "2026-05-27T00:00:00Z"
                    }
                }
            }
        }
    }
)
async def disconnect():
    """Bağlantıyı kes"""
    log = get_log_service()
    i18n = get_i18n_service()

    printer = get_printer()
    conn_type = printer.connection_type() if printer else None

    if printer and printer.connected:
        await printer.disconnect()
        set_printer(None)

    await log.log(op="disconnect", status="done", conn=conn_type)
    return ConnectResponse(
        status="disconnected",
        connection_type=None,
        message=i18n.t("status.disconnected"),
        timestamp=datetime.now(timezone.utc),
    )
