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
    AcoReceiptRequest,
)
from app.models.responses import JobResponse
from app.services.print_service import get_print_service

# Ana yazdırma endpoint'leri
router = APIRouter(
    prefix="/print",
    tags=["Yazdırma"],
)

# LLM destekli akıllı yazdırma (opsiyonel)
llm_router = APIRouter(
    prefix="/print",
    tags=["Yazdırma"],
)


@router.post(
    "/text",
    response_model=JobResponse,
    dependencies=[Depends(verify_token)],
    summary="Metin Yazdır",
    description="""
Termal yazıcıya formatlanmış metin satırları gönderir.

## Kullanım Alanları
- Fiş ve makbuz yazdırma
- Etiket oluşturma
- Bilgilendirme notları
- Geri dönüşüm makinesi ödül fişleri

## Özellikler
- **Metin Formatı**: Kalın, altı çizili yazı desteği
- **Hizalama**: Sola, ortaya veya sağa hizalama
- **Font Boyutu**: Normal, çift yükseklik, çift genişlik veya tam çift boyut
- **Otomatik Kesme**: Yazdırma sonrası kağıt otomatik kesilir
- **Idempotency**: Aynı job_id ile tekrar gönderirseniz işlem tekrarlanmaz

## Çoklu Dil Desteği
`language` parametresi ile hata mesajlarının dilini belirleyebilirsiniz:
- `tr`: Türkçe
- `en`: İngilizce
- `de`: Almanca
- `fr`: Fransızca
    """,
    response_description="Yazdırma işi başarıyla kuyruğa alındı veya tamamlandı",
    responses={
        200: {
            "description": "Yazdırma başarılı",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "receipt-001",
                        "status": "done",
                        "message": "Yazdırma işlemi başarıyla tamamlandı",
                        "timestamp": "2026-05-27T00:00:00Z"
                    }
                }
            }
        },
        503: {
            "description": "Yazıcı hatası",
            "content": {
                "application/json": {
                    "examples": {
                        "paper_out": {
                            "summary": "Kağıt Bitti",
                            "value": {
                                "detail": {
                                    "error": {
                                        "code": "PAPER_OUT",
                                        "detail": "Kağıt bitti. Lütfen kağıt yükleyin ve tekrar deneyin."
                                    },
                                    "job_id": "receipt-001"
                                }
                            }
                        },
                        "cover_open": {
                            "summary": "Kapak Açık",
                            "value": {
                                "detail": {
                                    "error": {
                                        "code": "COVER_OPEN",
                                        "detail": "Yazıcı kapağı açık. Lütfen kapatın."
                                    },
                                    "job_id": "receipt-001"
                                }
                            }
                        }
                    }
                }
            }
        }
    }
)
async def print_text(req: PrintTextRequest):
    """Metin yazdır"""
    try:
        return await get_print_service().print_text(req)
    except PrinterError as err:
        raise printer_error_to_http(err)


@router.post(
    "/image",
    response_model=JobResponse,
    dependencies=[Depends(verify_token)],
    summary="Görsel Yazdır",
    description="""
PNG veya JPEG formatında base64 kodlanmış görsel yazdırır.

## Kullanım Alanları
- Logo yazdırma
- Barkod ve QR kod görselleri
- Ürün resimleri
- Dekoratif grafikler

## Özellikler
- **Format Desteği**: PNG ve JPEG
- **Otomatik Boyutlandırma**: Görsel yazıcı genişliğine göre otomatik ölçeklenir
- **Maksimum Genişlik**: 576 piksel (80mm kağıt için, 203 DPI)
- **Hizalama**: Sola, ortaya veya sağa hizalama
- **Base64 Kodlama**: Görsel base64 string olarak gönderilir

## Görsel Hazırlama İpuçları
- Yüksek kontrastlı görseller daha iyi sonuç verir
- Siyah-beyaz veya gri tonlamalı görseller önerilir
- Maksimum genişlik 576px olmalıdır
- Dosya boyutunu küçük tutun (< 1MB)
    """,
    response_description="Görsel yazdırma işi başarıyla tamamlandı",
    responses={
        200: {
            "description": "Görsel yazdırma başarılı",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "image-001",
                        "status": "done",
                        "message": "Görsel yazdırma başarıyla tamamlandı",
                        "timestamp": "2026-05-27T00:00:00Z"
                    }
                }
            }
        },
        400: {
            "description": "Geçersiz görsel formatı",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "image_base64 geçerli base64 verisi olmalıdır"
                    }
                }
            }
        }
    }
)
async def print_image(req: PrintImageRequest):
    """Görsel yazdır"""
    try:
        return await get_print_service().print_image(req)
    except PrinterError as err:
        raise printer_error_to_http(err)


@router.post(
    "/qr",
    response_model=JobResponse,
    dependencies=[Depends(verify_token)],
    summary="QR Kod Yazdır",
    description="""
QR kod oluşturur ve yazdırır. URL, metin veya herhangi bir veri kodlanabilir.

## Kullanım Alanları
- Web sitesi URL'leri
- Ödeme linkleri
- Ürün takip kodları
- WiFi bağlantı bilgileri
- İletişim bilgileri (vCard)

## Özellikler
- **Boyut Ayarı**: 1-16 arası modül boyutu (6 önerilir)
- **Hata Düzeltme**: L (Düşük), M (Orta), Q (Yüksek), H (Çok Yüksek)
- **Etiket**: QR kodun altında açıklayıcı metin eklenebilir
- **Hizalama**: Sola, ortaya veya sağa hizalama
- **Maksimum Veri**: 2048 karakter

## Hata Düzeltme Seviyeleri
- **L (Low)**: %7 hata düzeltme - Temiz ortamlar için
- **M (Medium)**: %15 hata düzeltme - Genel kullanım (önerilen)
- **Q (Quartile)**: %25 hata düzeltme - Yıpranma riski varsa
- **H (High)**: %30 hata düzeltme - Zorlu koşullar için
    """,
    response_description="QR kod başarıyla yazdırıldı",
    responses={
        200: {
            "description": "QR kod yazdırma başarılı",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "qr-001",
                        "status": "done",
                        "message": "QR kod başarıyla yazdırıldı",
                        "timestamp": "2026-05-27T00:00:00Z"
                    }
                }
            }
        }
    }
)
async def print_qr(req: PrintQRRequest):
    """QR kod yazdır"""
    try:
        return await get_print_service().print_qr(req)
    except PrinterError as err:
        raise printer_error_to_http(err)


@llm_router.post(
    "/smart",
    response_model=JobResponse,
    dependencies=[Depends(verify_token)],
    summary="Akıllı Yazdırma (Yapay Zeka)",
    description="""
Yapay zeka destekli akıllı yazdırma özelliği. Yapılandırılmış JSON verisini otomatik olarak okunabilir fiş formatına dönüştürür.

## Nasıl Çalışır?
1. Yapılandırılmış JSON verisi gönderirsiniz
2. Yapay zeka, veriyi analiz eder ve uygun fiş formatına dönüştürür
3. Formatlanmış fiş otomatik olarak yazdırılır

## Kullanım Alanları
- Dinamik fiş içeriği oluşturma
- Farklı veri kaynaklarından fiş üretme
- Çoklu dil desteği ile otomatik çeviri
- Özel fiş şablonları oluşturma

## Yapılandırma
Bu özellik varsayılan olarak **kapalıdır**. Aktif etmek için `.env` dosyasında:

```env
LLM_ENABLED=true
GROQ_API_KEY=gsk_your_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

## Önemli Notlar
- Bu özellik dış API servisi kullanır (OpenRouter)
- API anahtarı gerektirir
- İnternet bağlantısı gereklidir
- LLM devre dışıysa basit anahtar-değer formatında yazdırır

## Dil Desteği
`language` parametresi ile çıktı dilini belirleyebilirsiniz:
- `tr`: Türkçe
- `en`: İngilizce
- `de`: Almanca
- `fr`: Fransızca
    """,
    response_description="Akıllı yazdırma başarıyla tamamlandı",
    responses={
        200: {
            "description": "Akıllı yazdırma başarılı",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "smart-001",
                        "status": "done",
                        "message": "Akıllı yazdırma başarıyla tamamlandı",
                        "timestamp": "2026-05-27T00:00:00Z"
                    }
                }
            }
        },
        503: {
            "description": "LLM servisi kullanılamıyor",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "LLM özelliği devre dışı. Basit format kullanılıyor."
                    }
                }
            }
        }
    }
)
async def print_smart(req: SmartPrintRequest):
    """Akıllı yazdırma (AI)"""
    try:
        return await get_print_service().print_smart(req)
    except PrinterError as err:
        raise printer_error_to_http(err)


@router.post(
    "/aco",
    response_model=JobResponse,
    dependencies=[Depends(verify_token)],
    summary="ACO Recycling Ödül Fişi Yazdır",
    description="""
ACO Recycling geri dönüşüm makinesi için standart ödül fişi yazdırır.

## Fiş İçeriği
- **Başlık**: ACO RECYCLING logosu (büyük font)
- **Makine Bilgisi**: MachineID ve UTC zaman damgası
- **Ödül Miktarı**: Büyük ve kalın font (TL/EUR/USD/GBP)
- **Ürün Tablosu**: Cam, Plastik, Metal, Tetrapak adet ve puan
- **QR Kod**: Büyük QR kodu (URL veya veri)

## Dil Desteği
`language` parametresi ile tüm etiketler çevrilir:
- `tr`: Türkçe (Cam, Plastik, Metal, Tetrapak, Ödül...)
- `en`: English (Glass, Plastic, Metal, Tetrapak, Reward...)
- `de`: Deutsch (Glas, Plastik, Metall, Tetrapak, Belohnung...)
- `fr`: Français (Verre, Plastique, Métal, Tetrapak, Récompense...)
    """,
    response_description="ACO fişi başarıyla yazdırıldı",
    responses={
        200: {
            "description": "Fiş yazdırma başarılı",
            "content": {
                "application/json": {
                    "example": {
                        "job_id": "aco-001",
                        "status": "done",
                        "message": "ACO receipt printed successfully.",
                        "timestamp": "2026-05-27T00:00:00Z"
                    }
                }
            }
        }
    }
)
async def print_aco(req: AcoReceiptRequest):
    """ACO Recycling ödül fişi yazdır"""
    try:
        return await get_print_service().print_aco(req)
    except PrinterError as err:
        raise printer_error_to_http(err)
