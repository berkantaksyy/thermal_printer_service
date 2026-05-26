"""
Yazıcı bağlantı endpoint'leri
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import verify_token
from app.core.printer import PrinterFactory, get_printer, set_printer, require_printer
from app.core.error_handler import PrinterError, printer_error_to_http
from app.models.requests import ConnectRequest
from app.models.responses import ConnectResponse
from app.services.log_service import get_log_service
from app.services.i18n_service import get_i18n_service

router = APIRouter(prefix="/connect", tags=["🔌 Bağlantı"])


@router.post("", response_model=ConnectResponse, dependencies=[Depends(verify_token)])
async def connect(req: ConnectRequest):
    """
    Yazıcıya bağlan (USB veya LAN).
    
    **USB Bağlantısı:**
    ```json
    {
      "connection_type": "usb"
    }
    ```
    
    **LAN Bağlantısı:**
    ```json
    {
      "connection_type": "lan",
      "lan_host": "192.168.1.100",
      "lan_port": 9100
    }
    ```
    
    Mevcut bağlantı varsa önce kesilir, sonra yeni bağlantı kurulur.
    """
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


@router.post("/disconnect", response_model=ConnectResponse, dependencies=[Depends(verify_token)])
async def disconnect():
    """
    Yazıcı bağlantısını kes.
    
    Aktif bağlantı varsa güvenli bir şekilde kesilir.
    """
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
