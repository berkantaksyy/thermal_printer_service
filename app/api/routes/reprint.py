"""
Yeniden yazdırma endpoint'i
"""

from fastapi import APIRouter, Depends

from app.api.deps import verify_token
from app.core.error_handler import PrinterError, printer_error_to_http
from app.models.requests import ReprintRequest
from app.models.responses import JobResponse
from app.services.print_service import get_print_service

router = APIRouter(tags=["Yeniden Yazdır"])


@router.post(
    "/reprint",
    response_model=JobResponse,
    dependencies=[Depends(verify_token)],
    summary="Başarısız İşi Yeniden Yazdır",
    description="""
Başarısız olan bir yazdırma işini yeniden dener.

## Nasıl Çalışır?

### 1. Otomatik Kaydetme
Bir yazdırma işi başarısız olduğunda (kağıt bitmesi, kapak açık, vb.), iş otomatik olarak `data/failed_jobs/` klasörüne kaydedilir.

### 2. Yeniden Yazdırma
Bu endpoint ile job_id kullanarak başarısız işi yeniden yazdırabilirsiniz. Orijinal parametreler korunur.

### 3. Otomatik Temizlik
Yeniden yazdırma başarılı olursa, iş otomatik olarak başarısız kuyruktan silinir.

## Kullanım Senaryoları

### Kağıt Bitmesi
1. Yazdırma sırasında kağıt biter
2. İş başarısız olarak kaydedilir
3. Kağıt yüklenir
4. Bu endpoint ile iş yeniden yazdırılır

### Kapak Açık
1. Yazdırma sırasında kapak açılır
2. İş başarısız olarak kaydedilir
3. Kapak kapatılır
4. İş yeniden yazdırılır

### Bağlantı Hatası
1. Geçici bağlantı sorunu oluşur
2. İş başarısız olarak kaydedilir
3. Bağlantı düzelir
4. İş yeniden yazdırılır

## Özellikler
- Orijinal iş parametreleri korunur
- Aynı job_id ile tekrar yazdırılır
- Başarılı olursa otomatik temizlenir
- Başarısız olursa kuyrukta kalır

## Dil Desteği
`language` parametresi ile hata mesajlarının dilini değiştirebilirsiniz.
    """,
    response_description="Yeniden yazdırma işi başarıyla tamamlandı",
    responses={
        200: {
            "description": "Yeniden yazdırma başarılı",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "receipt-001",
                        "status": "done",
                        "message": "İş başarıyla yeniden yazdırıldı",
                        "timestamp": "2026-05-27T00:00:00Z"
                    }
                }
            }
        },
        404: {
            "description": "İş bulunamadı",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Job ID 'receipt-001' bulunamadı. İş daha önce başarıyla yazdırılmış veya silinmiş olabilir."
                    }
                }
            }
        },
        503: {
            "description": "Yeniden yazdırma başarısız",
            "content": {
                "application/json": {
                    "example": {
                        "detail": {
                            "error": {
                                "code": "PAPER_OUT",
                                "detail": "Kağıt bitti. Lütfen kağıt yükleyin ve tekrar deneyin."
                            },
                            "job_id": "receipt-001"
                        }
                    }
                }
            }
        }
    }
)
async def reprint(req: ReprintRequest):
    """Başarısız işi yeniden yazdır"""
    try:
        return await get_print_service().reprint(req.job_id)
    except PrinterError as err:
        raise printer_error_to_http(err)
