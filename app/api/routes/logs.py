"""
Log yönetimi endpoint'leri
"""

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
import io

from app.api.deps import verify_token
from app.models.responses import LogsResponse
from app.services.log_service import get_log_service
from app.services.queue_service import get_queue_service

router = APIRouter(prefix="/logs", tags=["Loglar"])


@router.get(
    "",
    response_model=LogsResponse,
    dependencies=[Depends(verify_token)],
    summary="Log Kayıtlarını Listele",
    description="""
Tüm yazdırma işlemlerinin ve sistem olaylarının log kayıtlarını sayfalı olarak döner.

## Filtreleme Seçenekleri

### Duruma Göre Filtreleme (status)
- **done**: Başarıyla tamamlanan işlemler
- **failed**: Başarısız olan işlemler
- **info**: Bilgilendirme logları

### İşleme Göre Filtreleme (op)
İşlem türüne göre filtreleme yapabilirsiniz:
- `print_text`: Metin yazdırma
- `print_image`: Görsel yazdırma
- `print_qr`: QR kod yazdırma
- `print_smart`: Akıllı yazdırma
- `connect`: Bağlantı kurma
- `disconnect`: Bağlantı kesme

## Sayfalama
- **page**: Sayfa numarası (varsayılan: 1)
- **page_size**: Sayfa başına kayıt sayısı (varsayılan: 100, maksimum: 1000)

## Log Formatı
Her log kaydı şu bilgileri içerir:
- **ts**: Zaman damgası (ISO-8601 formatında)
- **op**: İşlem adı
- **conn**: Bağlantı tipi (usb/lan)
- **job_id**: İş kimliği
- **status**: İşlem durumu
- **error**: Hata detayı (varsa)

## Kullanım Senaryoları
- Hata ayıklama ve sorun giderme
- İşlem geçmişi takibi
- Performans analizi
- Denetim (audit) kayıtları
- Raporlama ve istatistik
    """,
    response_description="Sayfalı log kayıtları",
    responses={
        200: {
            "description": "Log kayıtları başarıyla alındı",
            "content": {
                "application/json": {
                    "example": {
                        "total": 150,
                        "entries": [
                            {
                                "ts": "2026-05-27T00:00:00Z",
                                "op": "print_text",
                                "conn": "usb",
                                "job_id": "receipt-001",
                                "status": "done",
                                "error": None
                            },
                            {
                                "ts": "2026-05-27T00:05:00Z",
                                "op": "print_text",
                                "conn": "usb",
                                "job_id": "receipt-002",
                                "status": "failed",
                                "error": {
                                    "code": "PAPER_OUT",
                                    "detail": "Kağıt bitti. Lütfen kağıt yükleyin."
                                }
                            }
                        ],
                        "page": 1,
                        "page_size": 100
                    }
                }
            }
        }
    }
)
async def get_logs(
    page: int = Query(1, ge=1, description="Sayfa numarası"),
    page_size: int = Query(100, ge=1, le=1000, description="Sayfa başına kayıt"),
    status: str | None = Query(None, description="Duruma göre filtrele: done|failed|info"),
    op: str | None = Query(None, description="İşleme göre filtrele"),
):
    """Log kayıtlarını listele"""
    log_svc = get_log_service()
    total, entries = await log_svc.get_entries(
        page=page,
        page_size=page_size,
        status_filter=status,
        op_filter=op,
    )
    return LogsResponse(total=total, entries=entries, page=page, page_size=page_size)


@router.get(
    "/export",
    dependencies=[Depends(verify_token)],
    summary="Logları CSV Olarak İndir",
    description="""
Tüm log kayıtlarını CSV formatında indirir.

## Özellikler
- Tüm log kayıtları tek seferde indirilir
- CSV formatı Excel ve diğer araçlarla uyumludur
- Dosya adı: `printer_logs.csv`

## CSV Sütunları
- Timestamp (Zaman)
- Operation (İşlem)
- Connection (Bağlantı)
- Job ID (İş Kimliği)
- Status (Durum)
- Error Code (Hata Kodu)
- Error Detail (Hata Detayı)

## Kullanım Alanları
- Uzun dönem analiz için veri arşivleme
- Excel'de pivot tablo ve grafik oluşturma
- Harici analiz araçlarına veri aktarımı
- Yedekleme ve raporlama
    """,
    response_description="CSV dosyası",
    responses={
        200: {
            "description": "CSV dosyası başarıyla oluşturuldu",
            "content": {
                "text/csv": {
                    "example": "timestamp,operation,connection,job_id,status,error_code,error_detail\n2026-05-27T00:00:00Z,print_text,usb,receipt-001,done,,\n"
                }
            }
        }
    }
)
async def export_logs():
    """Logları CSV olarak indir"""
    log_svc = get_log_service()
    csv_content = await log_svc.export_csv()
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="printer_logs.csv"'},
    )


@router.get(
    "/failed",
    dependencies=[Depends(verify_token)],
    summary="Başarısız İşleri Listele",
    description="""
Başarısız olan ve yeniden yazdırılmayı bekleyen işlerin listesini döner.

## Ne Zaman Kullanılır?
- Kağıt bitmesi nedeniyle başarısız olan işleri görmek için
- Yazıcı hatası sonrası bekleyen işleri kontrol etmek için
- Yeniden yazdırma işlemi öncesi listeyi görmek için

## Başarısız İş Yönetimi
1. İş başarısız olduğunda otomatik olarak `data/failed_jobs/` klasörüne kaydedilir
2. Bu endpoint ile başarısız işlerin listesini alabilirsiniz
3. `/reprint` endpoint'i ile işi yeniden yazdırabilirsiniz
4. Başarılı yazdırma sonrası iş otomatik olarak listeden silinir

## Dönen Bilgiler
- Job ID listesi
- Her iş için kaydedilme zamanı
- İşin orijinal parametreleri
    """,
    response_description="Başarısız iş listesi",
    responses={
        200: {
            "description": "Başarısız işler başarıyla listelendi",
            "content": {
                "application/json": {
                    "example": {
                        "failed_jobs": [
                            "receipt-001",
                            "receipt-002",
                            "qr-005"
                        ]
                    }
                }
            }
        }
    }
)
async def list_failed_jobs():
    """Başarısız işleri listele"""
    queue = get_queue_service()
    return {"failed_jobs": await queue.list_failed()}
