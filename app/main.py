"""
Thermal Printer Service — FastAPI Application Entry Point

Cashino KP-300 / KP-301H REST API Service
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import get_settings
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
        title="🖨️ Termal Yazıcı Servisi",
        version=settings.app_version,
        description=(
            "**Cashino KP-300 / KP-301H** termal yazıcılar için REST API servisi.\n\n"
            "### Özellikler\n"
            "- 🔌 USB ve LAN bağlantı desteği\n"
            "- 📝 Metin, görsel ve QR kod yazdırma\n"
            "- 🤖 Yapay zeka destekli akıllı yazdırma (opsiyonel)\n"
            "- 🌍 Çoklu dil desteği (TR/EN/DE/FR)\n"
            "- 📊 Detaylı loglama ve kuyruk yönetimi\n\n"
            "### Kimlik Doğrulama\n"
            "`/health` endpoint'i hariç tüm istekler Bearer token gerektirir:\n"
            "```\nAuthorization: Bearer your-token-here\n```\n\n"
            "Token'ı `.env` dosyasında `API_BEARER_TOKEN` ile ayarlayın."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
        swagger_ui_parameters={
            "defaultModelsExpandDepth": -1,  # Model şemalarını gizle
            "docExpansion": "list",  # Endpoint'leri liste olarak göster
            "filter": True,  # Arama kutusu ekle
            "syntaxHighlight.theme": "monokai",  # Dark tema
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

    # ── Static UI ─────────────────────────────────────────────────────────────
    if os.path.isdir("ui"):
        app.mount("/ui", StaticFiles(directory="ui", html=True), name="ui")

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
