"""
Kağıt rulo yönetimi endpoint'leri
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.api.deps import verify_token
from app.models.responses import PaperStatsResponse
from app.services.paper_service import get_paper_service
from app.services.i18n_service import get_i18n_service

router = APIRouter(prefix="/paper", tags=["Kağıt Rulo"])


@router.get(
    "",
    response_model=PaperStatsResponse,
    dependencies=[Depends(verify_token)],
    summary="Rulo Durumunu Sorgula",
    description="""
Kağıt rulo kullanım tahminini döner.

> ⚠️ **Tüm değerler tahmindir.** Yazıcı gerçek kağıt uzunluğunu raporlamaz.
> Her baskı işleminin kağıt tüketimi hesaplanarak biriktirilir.

## Dönüş Değerleri
- **remaining_pct**: Kalan kağıt yüzdesi (0-100)
- **remaining_m**: Kalan tahmini metre
- **prints_remaining**: Ortalama baskı boyutuna göre tahmini kalan baskı sayısı
- **print_count**: Bu ruloya yapılan toplam baskı sayısı
    """,
)
async def get_paper_stats():
    """Rulo kağıt kullanım tahminini döner"""
    stats = get_paper_service().get_stats()
    return PaperStatsResponse(**stats)


@router.post(
    "/reset",
    dependencies=[Depends(verify_token)],
    summary="Yeni Rulo Takıldı",
    description="""
Yeni rulo takıldığında çağrılır. Kullanım sayacını sıfırlar.

`total_roll_mm` ile farklı bir rulo boyu belirtilebilir (varsayılan: 80 000 mm = 80 m).
    """,
)
async def reset_paper(
    total_roll_mm: Optional[float] = Query(
        None,
        description="Yeni rulo uzunluğu (mm). Boş bırakılırsa önceki değer korunur.",
        ge=1000,
        le=500_000,
    ),
    language: str = Query("tr", description="Dil kodu"),
):
    """Yeni rulo sıfırlama"""
    get_paper_service().reset_roll(total_roll_mm)
    i18n = get_i18n_service()
    return {"message": i18n.t("paper.reset_done", lang=language)}
