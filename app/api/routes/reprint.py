"""
Yeniden yazdırma endpoint'i
"""

from fastapi import APIRouter, Depends

from app.api.deps import verify_token
from app.core.error_handler import PrinterError, printer_error_to_http
from app.models.requests import ReprintRequest
from app.models.responses import JobResponse
from app.services.print_service import get_print_service

router = APIRouter(tags=["🔄 Yeniden Yazdır"])


@router.post("/reprint", response_model=JobResponse, dependencies=[Depends(verify_token)])
async def reprint(req: ReprintRequest):
    """
    Başarısız bir işi yeniden yazdır.
    
    **Nasıl Çalışır:**
    1. İş başarısız olduğunda otomatik olarak `data/failed_jobs/` klasörüne kaydedilir
    2. Bu endpoint ile job_id kullanarak yeniden yazdırabilirsiniz
    3. Başarılı olursa, iş başarısız kuyruktan silinir
    
    **Örnek:**
    ```json
    {
      "job_id": "receipt-001"
    }
    ```
    """
    try:
        return await get_print_service().reprint(req.job_id)
    except PrinterError as err:
        raise printer_error_to_http(err)
