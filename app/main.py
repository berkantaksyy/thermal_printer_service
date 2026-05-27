"""
Thermal Printer Service — FastAPI Application Entry Point

Cashino KP-300 / KP-301H REST API Service
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import get_settings
from app.core.i18n_openapi import get_translated_openapi, TRANSLATIONS
from app.core.endpoint_i18n import get_endpoint_translation
from app.api.routes import connection, print as print_router, status, logs, health, reprint
from app.api.routes.print import llm_router as print_llm_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    settings = get_settings()
    logger.info(f"Starting {settings.app_title} v{settings.app_version}")
    logger.info(f"LLM integration: {'ENABLED' if settings.llm_enabled else 'disabled'}")
    logger.info(f"Default connection: {settings.default_connection_type}")
    yield
    # Graceful shutdown: disconnect printer
    from app.core.printer import get_printer
    printer = get_printer()
    if printer and printer.connected:
        await printer.disconnect()
    logger.info("Thermal Printer Service stopped.")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Termal Yazıcı Servisi API",
        version=settings.app_version,
        description="""
# Cashino KP-300 / KP-301H Termal Yazıcı REST API

Profesyonel termal yazıcı yönetimi için eksiksiz REST API servisi.

## Temel Özellikler

### Bağlantı Yönetimi
- **USB Bağlantı**: Plug-and-play USB desteği
- **LAN Bağlantı**: Ağ üzerinden IP/Port ile bağlantı
- **Otomatik Yeniden Bağlanma**: Bağlantı kopması durumunda otomatik deneme

### Yazdırma Yetenekleri
- **Metin Yazdırma**: Formatlanmış metin satırları (kalın, altı çizili, hizalama, font boyutu)
- **Görsel Yazdırma**: PNG/JPEG formatında base64 kodlu görseller
- **QR Kod**: Özelleştirilebilir boyut ve hata düzeltme seviyesi
- **Akıllı Yazdırma**: Yapay zeka destekli otomatik fiş formatı (opsiyonel)

### Sistem Özellikleri
- **Çoklu Dil**: Türkçe, İngilizce, Almanca, Fransızca
- **Detaylı Loglama**: JSON formatında yapılandırılmış loglar
- **Kuyruk Yönetimi**: Başarısız işleri yeniden yazdırma
- **Durum İzleme**: Gerçek zamanlı yazıcı durumu ve metrikler

## Kimlik Doğrulama

Tüm endpoint'ler (sadece `/health` hariç) Bearer token ile korunmaktadır:

```
Authorization: Bearer your-secret-token
```

Token'ı `.env` dosyasında `API_BEARER_TOKEN` değişkeni ile ayarlayın.

## Hızlı Başlangıç

1. Yazıcıya bağlanın: `POST /connect`
2. Durum kontrolü yapın: `GET /status`
3. Yazdırma işlemi gönderin: `POST /print/text`
4. Logları kontrol edin: `GET /logs`

## Hata Yönetimi

Tüm hatalar standart HTTP durum kodları ve detaylı hata mesajları ile döner:
- **400**: Geçersiz istek parametreleri
- **401**: Kimlik doğrulama hatası
- **404**: Kaynak bulunamadı
- **503**: Yazıcı hatası (kağıt bitti, kapak açık, vb.)

## Dil Desteği

Her endpoint `language` parametresi ile dil seçimi yapabilir:
- `tr`: Türkçe
- `en`: English
- `de`: Deutsch
- `fr`: Français

Varsayılan dil `.env` dosyasında `DEFAULT_LANGUAGE` ile ayarlanır.

## Teknik Detaylar

- **Framework**: FastAPI (Python)
- **Yazıcı Protokolü**: ESC/POS
- **Bağlantı**: USB (pyusb) ve LAN (asyncio TCP)
- **Log Formatı**: JSON Lines
- **Donanım**: Cashino KP-300 / KP-301H (80mm, 203 DPI)
        """,
        docs_url=None,  # Disable default docs
        redoc_url="/redoc",
        lifespan=lifespan,
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1,
            "docExpansion": "none",
            "filter": True,
            "syntaxHighlight.theme": "monokai",
            "displayRequestDuration": True,
            "persistAuthorization": True,
            "tryItOutEnabled": True,
            "deepLinking": True,
            "displayOperationId": False,
        }
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(health.router)
    app.include_router(status.router)
    app.include_router(connection.router)
    app.include_router(print_router.router)      # Option 1: standard endpoints
    app.include_router(print_llm_router)          # Option 2: LLM endpoint
    app.include_router(reprint.router)
    app.include_router(logs.router)

    # ── Static Files ──────────────────────────────────────────────────────────
    if os.path.isdir("app/static"):
        app.mount("/static", StaticFiles(directory="app/static"), name="static")
    
    # ── Static UI ─────────────────────────────────────────────────────────────
    if os.path.isdir("ui"):
        app.mount("/ui", StaticFiles(directory="ui", html=True), name="ui")

    # ── Custom OpenAPI with i18n ──────────────────────────────────────────────
    @app.get("/openapi.json", include_in_schema=False)
    async def get_openapi_with_lang(language: str = Query("tr", description="API dili: tr, en, de, fr")):
        """Dile göre özelleştirilmiş OpenAPI spec döndürür"""
        from fastapi.openapi.utils import get_openapi
        
        # Dil çevirisini al
        trans = get_translated_openapi(language)
        
        # OpenAPI spec'ini oluştur (cache kullanmıyoruz - her seferinde yeniden oluştur)
        # Bu sayede güncellemeler anında yansır
        if True:  # Her zaman yeniden oluştur
            openapi_schema = get_openapi(
                title=trans["title"],
                version=settings.app_version,
                description=trans["description"],
                routes=app.routes,
            )
            
            # Tag açıklamalarını çevir
            if "tags" in openapi_schema:
                for tag in openapi_schema["tags"]:
                    tag_name = tag["name"]
                    if tag_name in trans["tags"]:
                        tag["description"] = trans["tags"][tag_name]
            
            # Endpoint açıklamalarını çevir
            if "paths" in openapi_schema:
                for path, methods in openapi_schema["paths"].items():
                    for method, details in methods.items():
                        if method in ["get", "post", "put", "delete", "patch"]:
                            # Logs endpoints
                            if path == "/logs" and method == "get":
                                t = get_endpoint_translation("logs", "get_logs", language)
                                details["summary"] = t["summary"]
                                details["description"] = t["description"]
                                if "responses" in details and "200" in details["responses"]:
                                    details["responses"]["200"]["description"] = t["response_description"]
                            
                            elif path == "/logs/export" and method == "get":
                                t = get_endpoint_translation("logs", "export_logs", language)
                                details["summary"] = t["summary"]
                                details["description"] = t["description"]
                                if "responses" in details and "200" in details["responses"]:
                                    details["responses"]["200"]["description"] = t["response_description"]
                            
                            elif path == "/logs/failed" and method == "get":
                                t = get_endpoint_translation("logs", "list_failed_jobs", language)
                                details["summary"] = t["summary"]
                                details["description"] = t["description"]
                                if "responses" in details and "200" in details["responses"]:
                                    details["responses"]["200"]["description"] = t["response_description"]
                            
                            # Reprint endpoint
                            elif path == "/reprint" and method == "post":
                                t = get_endpoint_translation("reprint", "reprint", language)
                                details["summary"] = t["summary"]
                                details["description"] = t["description"]
                                if "responses" in details and "200" in details["responses"]:
                                    details["responses"]["200"]["description"] = t["response_description"]
            
        return openapi_schema
    
    # ── Custom Swagger UI ─────────────────────────────────────────────────────
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui():
        """Custom Swagger UI with enhanced design"""
        try:
            with open("app/static/swagger-ui.html", "r", encoding="utf-8") as f:
                html_content = f.read()
            return HTMLResponse(content=html_content)
        except FileNotFoundError:
            return HTMLResponse(
                content="<h1>Swagger UI bulunamadı</h1><p>Lütfen app/static/swagger-ui.html dosyasını kontrol edin.</p>",
                status_code=404
            )

    # ── Root redirect ─────────────────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    async def root():
        return {"service": settings.app_title, "version": settings.app_version, "docs": "/docs", "ui": "/ui"}

    # ── Global error handler ──────────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled error on {request.url}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "INTERNAL_ERROR", "detail": str(exc)}},
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
        log_level="info",
    )
