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

router = APIRouter(prefix="/logs", tags=["📝 Loglar"])


@router.get("", response_model=LogsResponse, dependencies=[Depends(verify_token)])
async def get_logs(
    page: int = Query(1, ge=1, description="Sayfa numarası"),
    page_size: int = Query(100, ge=1, le=1000, description="Sayfa başına kayıt"),
    status: str | None = Query(None, description="Duruma göre filtrele: done|failed|info"),
    op: str | None = Query(None, description="İşleme göre filtrele"),
):
    """
    Logları listele (sayfalı).
    
    **Filtreleme:**
    - `status`: done, failed veya info
    - `op`: İşlem adı (print_text, connect, vb.)
    
    **Sayfalama:**
    - `page`: Sayfa numarası (varsayılan: 1)
    - `page_size`: Sayfa başına kayıt (varsayılan: 100, max: 1000)
    """
    log_svc = get_log_service()
    total, entries = await log_svc.get_entries(
        page=page,
        page_size=page_size,
        status_filter=status,
        op_filter=op,
    )
    return LogsResponse(total=total, entries=entries, page=page, page_size=page_size)


@router.get("/export", dependencies=[Depends(verify_token)])
async def export_logs():
    """
    Tüm logları CSV olarak indir.
    
    Dosya adı: `printer_logs.csv`
    """
    log_svc = get_log_service()
    csv_content = await log_svc.export_csv()
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="printer_logs.csv"'},
    )


@router.get("/failed", dependencies=[Depends(verify_token)])
async def list_failed_jobs():
    """
    Başarısız işleri listele.
    
    Başarısız olan ve yeniden yazdırılmayı bekleyen işlerin listesini döner.
    """
    queue = get_queue_service()
    return {"failed_jobs": await queue.list_failed()}
