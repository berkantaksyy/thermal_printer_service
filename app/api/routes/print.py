"""
Yazdırma endpoint'leri
"""

from fastapi import APIRouter, Depends

from app.api.deps import verify_token
from app.core.error_handler import PrinterError, printer_error_to_http
from app.models.requests import (
    PrintTextRequest,
    PrintImageRequest,
    PrintQRRequest,
    SmartPrintRequest,
)
from app.models.responses import JobResponse
from app.services.print_service import get_print_service

# Ana yazdırma endpoint'leri
router = APIRouter(
    prefix="/print",
    tags=["🖨️ Yazdırma"],
)

# LLM destekli akıllı yazdırma (opsiyonel)
llm_router = APIRouter(
    prefix="/print",
    tags=["🖨️ Yazdırma"],
)


@router.post(
    "/text",
    response_model=JobResponse,
    dependencies=[Depends(verify_token)],
    summary="📝 Metin Yazdır",
)
async def print_text(req: PrintTextRequest):
    """
    Bir veya daha fazla metin satırını yazdırır.
    
    **Özellikler:**
    - Kalın, altı çizili metin desteği
    - Hizalama: sol, orta, sağ
    - Font boyutu: normal, çift yükseklik, çift genişlik, çift
    - Otomatik kağıt kesme
    
    **İpucu:** Aynı `job_id` ile tekrar gönderirseniz, işlem tekrarlanmaz (idempotent).
    """
    try:
        return await get_print_service().print_text(req)
    except PrinterError as err:
        raise printer_error_to_http(err)


@router.post(
    "/image",
    response_model=JobResponse,
    dependencies=[Depends(verify_token)],
    summary="🖼️ Görsel Yazdır",
)
async def print_image(req: PrintImageRequest):
    """
    PNG veya JPEG formatında base64 kodlanmış görsel yazdırır.
    
    **Özellikler:**
    - Otomatik boyutlandırma (yazıcı genişliğine göre)
    - Hizalama desteği
    - Maksimum genişlik: 576px (80mm kağıt için)
    """
    try:
        return await get_print_service().print_image(req)
    except PrinterError as err:
        raise printer_error_to_http(err)


@router.post(
    "/qr",
    response_model=JobResponse,
    dependencies=[Depends(verify_token)],
    summary="⬛ QR Kod Yazdır",
)
async def print_qr(req: PrintQRRequest):
    """
    QR kod yazdırır (URL, metin veya herhangi bir veri).
    
    **Özellikler:**
    - Boyut ayarlanabilir (1-16)
    - Hata düzeltme seviyesi: L, M, Q, H
    - Opsiyonel etiket (QR kodun altında görünür)
    - Hizalama desteği
    """
    try:
        return await get_print_service().print_qr(req)
    except PrinterError as err:
        raise printer_error_to_http(err)


@llm_router.post(
    "/smart",
    response_model=JobResponse,
    dependencies=[Depends(verify_token)],
    summary="🤖 Akıllı Yazdırma (AI)",
)
async def print_smart(req: SmartPrintRequest):
    """
    JSON veri gönder, yapay zeka fiş formatına dönüştürsün.
    
    **Nasıl Çalışır:**
    1. Yapılandırılmış JSON verisi gönderirsiniz
    2. AI, veriyi okunabilir fiş formatına dönüştürür
    3. Fiş yazdırılır
    
    **Yapılandırma (.env dosyası):**
    ```
    LLM_ENABLED=true
    GROQ_API_KEY=gsk_...
    GROQ_MODEL=llama3-8b-8192
    ```
    
    **Not:** LLM devre dışıysa, basit anahtar-değer formatında yazdırır.
    
    ⚠️ **Uyarı:** Bu özellik dış API kullanır (Groq). Varsayılan olarak kapalıdır.
    """
    try:
        return await get_print_service().print_smart(req)
    except PrinterError as err:
        raise printer_error_to_http(err)
