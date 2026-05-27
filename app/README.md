# 🗂️ app/ — FastAPI Backend

<div align="center">

[![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python)](https://python.org)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063?style=flat-square)](https://docs.pydantic.dev/)

[🇹🇷 Türkçe](#türkçe) · [🇬🇧 English](#english) · [🇩🇪 Deutsch](#deutsch) · [🇫🇷 Français](#français)

</div>

---

<a id="türkçe"></a>

## 🇹🇷 Türkçe

### Mimari Genel Bakış

```
app/
├── main.py                      # FastAPI uygulama başlangıcı, CORS, router kayıtları
├── api/
│   ├── deps.py                  # Bearer token kimlik doğrulama bağımlılığı
│   └── routes/
│       ├── connection.py        # POST /connect, /connect/disconnect
│       ├── health.py            # GET /health (auth yok — Docker health check)
│       ├── logs.py              # GET /logs, /logs/export, /logs/failed
│       ├── paper.py             # GET /paper/stats, POST /paper/reset
│       ├── print.py             # POST /print/text, /image, /qr, /smart
│       ├── reprint.py           # POST /reprint
│       └── status.py            # GET /status
├── core/
│   ├── config.py                # pydantic-settings ile ortam değişkenleri
│   ├── endpoint_i18n.py         # OpenAPI i18n yardımcısı
│   ├── error_handler.py         # PrinterError + hata kodu metadata'sı
│   ├── escpos_engine.py         # ESC/POS komut oluşturucu
│   ├── i18n_openapi.py          # Swagger açıklamalarını çevir
│   ├── lan_printer.py           # asyncio TCP LAN backend
│   ├── printer.py               # Soyut PrinterBase + fabrika fonksiyonu
│   └── usb_printer.py           # pyusb USB backend
├── models/
│   ├── requests.py              # Pydantic v2 istek modelleri
│   └── responses.py             # Pydantic v2 yanıt modelleri
├── services/
│   ├── i18n_service.py          # Dil çevirisi yükleyici
│   ├── llm_service.py           # OpenRouter LLM entegrasyonu (opsiyonel)
│   ├── log_service.py           # JSONL loglama + CSV dışa aktarma
│   ├── paper_service.py         # Kağıt rulo tahmin servisi
│   ├── print_service.py         # Yazdırma iş akışı orkestrasyonu
│   └── queue_service.py         # Bellek içi kuyruk + başarısız iş kalıcılığı
└── i18n/
    ├── en.json                  # İngilizce çeviriler
    ├── tr.json                  # Türkçe çeviriler
    ├── de.json                  # Almanca çeviriler
    └── fr.json                  # Fransızca çeviriler
```

---

### Modüller Detaylı Açıklama

#### `main.py` — Uygulama Giriş Noktası

`FastAPI` uygulamasını oluşturur, tüm router'ları kaydeder, middleware'leri yapılandırır ve statik dosyaları (`/static`, `/ui`) mount eder.

- **CORS** middleware aktif (tüm origin'lere izin verilir — üretim için kısıtlayın)
- **Swagger UI** `/docs` adresine özel HTML ile yönlendirilir
- **OpenAPI JSON** `/openapi.json?language={lang}` ile dil parametresi alır

```python
# Route kayıtları
app.include_router(connection.router, tags=["Connection"])
app.include_router(print_router.router, prefix="/print", tags=["Print"])
app.include_router(status.router, tags=["Status"])
app.include_router(logs.router, tags=["Logs"])
app.include_router(health.router, tags=["Health"])
app.include_router(reprint.router, tags=["Reprint"])
app.include_router(paper.router, prefix="/paper", tags=["Paper"])
```

---

#### `api/deps.py` — Kimlik Doğrulama

Tüm korunan endpoint'lerde kullanılan `require_token` bağımlılığını sağlar.

```python
async def require_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != settings.API_BEARER_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
```

---

#### `core/config.py` — Konfigürasyon

`pydantic-settings` kullanarak `.env` dosyasından ve ortam değişkenlerinden ayarları okur.

| Ayar | Tür | Açıklama |
|------|-----|----------|
| `APP_HOST` | str | Sunucu bind adresi |
| `APP_PORT` | int | Sunucu portu |
| `APP_DEBUG` | bool | Hot-reload |
| `API_BEARER_TOKEN` | str | Bearer kimlik doğrulama tokeni |
| `DEFAULT_CONNECTION_TYPE` | str | `usb` \| `lan` |
| `USB_VENDOR_ID` | str | USB vendor ID (hex) |
| `USB_PRODUCT_ID` | str | USB product ID (hex) |
| `LAN_HOST` | str | LAN yazıcı IP |
| `LAN_PORT` | int | LAN yazıcı portu |
| `RECONNECT_MAX_RETRIES` | int | Maksimum yeniden bağlanma |
| `RECONNECT_BACKOFF_BASE` | float | Backoff tabanı (saniye) |
| `RECONNECT_BACKOFF_MAX` | float | Maksimum gecikme (saniye) |
| `LOG_DIR` | str | Log dizini |
| `LOG_KEEP_DAYS` | int | Log tutma süresi |
| `DEFAULT_LANGUAGE` | str | Varsayılan dil kodu |
| `LLM_ENABLED` | bool | LLM özelliği etkin mi |
| `OPENROUTER_API_KEY` | str | OpenRouter API anahtarı |
| `OPENROUTER_MODEL` | str | LLM modeli |

---

#### `core/escpos_engine.py` — ESC/POS Komut Oluşturucu

Termal yazıcı için ham byte dizileri oluşturur. Cashino KP-300/KP-301H'ı tam destekler.

| Metod | Açıklama |
|-------|----------|
| `init()` | Yazıcıyı başlat (`ESC @`) |
| `text_line(text, bold, align, font_size)` | Formatlı metin satırı |
| `feed_lines(n)` | `n` satır boşluk besle |
| `cut(partial)` | Kağıt kes (`GS V`) |
| `qr_code(data, size, error_correction)` | QR kod (`GS ( k`) |
| `image(pil_image, align)` | Raster görsel (`GS v 0`) |
| `build_receipt(lines, cut)` | Tam fiş bayt dizisi |

**Karakter Kodlama:** Türkçe karakterler (Ç, Ğ, İ, Ö, Ş, Ü) için `cp857` (IBM PC Türkçe) kodlaması kullanılır.

**Yazı Tipi Boyutları:**
- `normal` — standart
- `double` — iki kat genişlik+yükseklik (`GS !`)

---

#### `core/printer.py` — Soyut Temel Sınıf

```python
class PrinterBase(ABC):
    @abstractmethod
    async def connect(self) -> None: ...
    
    @abstractmethod
    async def disconnect(self) -> None: ...
    
    @abstractmethod
    async def write(self, data: bytes) -> None: ...
    
    @property
    @abstractmethod
    def is_connected(self) -> bool: ...
```

`get_printer(connection_type)` fabrika fonksiyonu `usb` veya `lan` için uygun backend'i döner.

---

#### `core/usb_printer.py` — USB Backend

`pyusb` kütüphanesini kullanır. USB bulk transfer ile ESC/POS bayt gönderir.

- **Auto-reconnect:** Bağlantı kesildiğinde `RECONNECT_MAX_RETRIES` × `RECONNECT_BACKOFF_BASE` (exponential) deneme
- **Vendor/Product ID:** `.env` üzerinden yapılandırılabilir
- **Kernel driver detach:** Linux'ta otomatik kernel driver ayırma

---

#### `core/lan_printer.py` — LAN Backend

`asyncio.open_connection()` ile TCP stream kullanır.

- **Raw port 9100:** Standart termal yazıcı ham yazdırma portu
- **Async write:** Tüm I/O işlemleri async/await ile gerçekleştirilir
- **Auto-reconnect:** USB backend ile aynı mantık

---

#### `core/error_handler.py` — Hata Yönetimi

```python
class PrinterError(Exception):
    def __init__(self, code: ErrorCode, detail: str = None): ...
```

| Hata Kodu | HTTP Status | Açıklama |
|-----------|------------|----------|
| `PAPER_OUT` | 503 | Kağıt bitti |
| `PAPER_JAM` | 503 | Kağıt sıkışması |
| `COVER_OPEN` | 503 | Kapak açık |
| `OVERHEAT` | 503 | Aşırı ısınma |
| `COMM_ERROR` | 502 | İletişim hatası |
| `UNKNOWN_COMMAND` | 400 | Geçersiz komut |

Tüm hata kodlarının mesajları 4 dilde (`app/i18n/*.json`) saklanır.

---

#### `services/print_service.py` — Yazdırma Orkestrasyonu

Merkezi yazdırma servisi. Tüm `/print/*` endpoint'leri bu servisi kullanır.

```python
class PrintService:
    async def print_text(job_id, lines, cut, language) -> JobRecord
    async def print_image(job_id, image_base64, align, cut, language) -> JobRecord  
    async def print_qr(job_id, data, size, error_correction, align, label, cut, language) -> JobRecord
    async def print_smart(job_id, data, template_hint, language) -> JobRecord
```

**İş Akışı:**
1. `QueueService.enqueue()` ile idempotency kontrolü
2. Yazıcı bağlantısı kontrolü
3. `EscposEngine` ile bayt dizisi oluştur
4. `printer.write()` ile gönder
5. `LogService.log_success()` ile logla
6. Hata durumunda: `QueueService.save_failed()` + `LogService.log_failure()`

---

#### `services/queue_service.py` — Kuyruk Servisi

```python
class QueueService:
    async def enqueue(op, payload, job_id) -> JobRecord  # idempotency korumalı
    async def get_next(timeout) -> Optional[JobRecord]
    def queue_size() -> int
    async def save_failed(rec, error) -> None            # data/failed_jobs/ disk'e yaz
    async def get_failed(job_id) -> Optional[JobRecord] # disk'ten oku
    async def delete_failed(job_id) -> bool             # başarılı reprint sonrası sil
    async def list_failed() -> list[dict]
```

**İdempotency Mekanizması:** Her `job_id` `_seen_ids` set'inde tutulur. Aynı `job_id` ile gelen ikinci istek `is_duplicate=True` döner — yazıcıya tekrar gönderilmez.

---

#### `services/log_service.py` — Loglama Servisi

Her yazdırma işlemi `logs/printer_service.jsonl` dosyasına JSON Lines formatında kaydedilir.

```json
{
  "ts": "2025-09-16T16:19:02.123Z",
  "op": "print_text",
  "conn": "usb",
  "jobId": "receipt-001",
  "status": "done",
  "error": null
}
```

- **CSV Dışa Aktarma:** `/logs/export` endpoint'i tüm logları CSV olarak döner
- **Sayfalama:** `page` + `page_size` parametreleri
- **Filtreleme:** `status` (`done`/`failed`/`info`) ve `op` ile filtre

---

#### `services/paper_service.py` — Kağıt Rulo Tahmini

```python
class PaperService:
    def get_stats() -> PaperStats
    # - remaining_m: kalan metre
    # - remaining_pct: kalan yüzde
    # - prints_remaining: tahmini baskı sayısı
    # - print_count: toplam baskı sayısı
    # - avg_m_per_print: baskı başına ortalama metre
    # - is_low: düşük stok uyarısı (bool)
    # - is_critical: kritik stok (bool)
    
    def reset() -> None  # Yeni rulo taktıktan sonra sayacı sıfırla
    def record_print(bytes_printed) -> None  # Her başarılı baskıda çağrılır
```

Veriler `data/paper_stats.json` dosyasına kalıcı olarak kaydedilir.

---

#### `services/i18n_service.py` — Dil Servisi

```python
def get_translation(language: str, key: str) -> str:
    # app/i18n/{language}.json dosyasından anahtarı çeker
    # Anahtar bulunamazsa İngilizceye düşer
    # İngilizce de yoksa key'i döner
```

Desteklenen diller: `en`, `tr`, `de`, `fr`

Her istek `language` parametresi ile dil belirtebilir. Belirtilmezse `DEFAULT_LANGUAGE` kullanılır.

---

#### `services/llm_service.py` — LLM Servisi (Opsiyonel)

`LLM_ENABLED=true` ayarlandığında aktif olur. OpenRouter API üzerinden herhangi bir modeli kullanabilir.

```python
class LLMService:
    async def generate_receipt_lines(data: dict, template_hint: str, language: str) -> list[LineItem]:
        # 1. JSON verisi → LLM prompt
        # 2. LLM yanıtı → satır listesi
        # 3. LLM başarısız olursa → _fallback_format() basit anahtar-değer formatı
```

**Fallback:** LLM devre dışıysa veya hata verirse, `_fallback_format()` tüm dillerde düzgün biçimli bir fiş oluşturur.

---

### i18n Dosya Yapısı

`app/i18n/*.json` dosyaları **backend API yanıtları** için kullanılır.

```json
{
  "error": {
    "PAPER_OUT": "Kağıt bitti. Lütfen kağıt yükleyin ve tekrar deneyin.",
    "PAPER_JAM": "Kağıt sıkışması. Lütfen kağıdı çıkarın.",
    ...
  },
  "status": {
    "connected": "Yazıcı bağlı",
    "disconnected": "Yazıcı bağlı değil"
  }
}
```

> **Not:** `ui/i18n/*.json` web dashboard için ayrı çeviri dosyalarıdır. Her iki set de güncel tutulmalıdır.

---

### API Endpoint'leri Detaylı

#### `POST /connect`

```json
{ "connection_type": "usb" }
// veya
{ "connection_type": "lan", "lan_host": "192.168.1.100", "lan_port": 9100 }
```

#### `POST /print/text`

```json
{
  "job_id": "string (opsiyonel — belirtilmezse UUID üretilir)",
  "lines": [
    {
      "text": "string",
      "bold": false,
      "align": "left | center | right",
      "font_size": "normal | double"
    }
  ],
  "cut": true,
  "language": "tr | en | de | fr"
}
```

#### `POST /print/qr`

```json
{
  "job_id": "string (opsiyonel)",
  "data": "string",
  "size": 6,
  "error_correction": "L | M | Q | H",
  "align": "left | center | right",
  "label": "string (opsiyonel)",
  "cut": true,
  "language": "tr"
}
```

#### `POST /print/image`

```json
{
  "job_id": "string (opsiyonel)",
  "image_base64": "base64 string (PNG veya JPEG)",
  "align": "left | center | right",
  "cut": true,
  "language": "tr"
}
```

#### `GET /logs`

Query parametreleri:
- `page` (varsayılan: 1)
- `page_size` (varsayılan: 100, max: 1000)
- `status` — `done` | `failed` | `info`
- `op` — işlem adı ile filtrele

---

<a id="english"></a>

<details>
<summary>🇬🇧 English — Click to expand</summary>

## English

### Architecture Overview

```
app/
├── main.py              # FastAPI app entry, CORS, router registration
├── api/
│   ├── deps.py          # Bearer token auth dependency
│   └── routes/          # All API route handlers
├── core/
│   ├── config.py        # pydantic-settings env config
│   ├── escpos_engine.py # ESC/POS byte command builder
│   ├── printer.py       # Abstract base + factory
│   ├── usb_printer.py   # USB backend (pyusb)
│   ├── lan_printer.py   # LAN backend (asyncio TCP)
│   └── error_handler.py # Error codes + PrinterError exception
├── models/
│   ├── requests.py      # Pydantic v2 request models
│   └── responses.py     # Pydantic v2 response models
├── services/
│   ├── print_service.py # Print workflow orchestration
│   ├── log_service.py   # JSONL logging + CSV export
│   ├── queue_service.py # In-memory queue + failed job persistence
│   ├── i18n_service.py  # Translation loader
│   ├── paper_service.py # Paper roll estimation
│   └── llm_service.py   # Optional OpenRouter LLM
└── i18n/
    ├── en.json / tr.json / de.json / fr.json
```

### Key Design Decisions

**Async throughout:** All I/O operations (printer writes, file reads, HTTP calls) use `async/await`. The printer connection is a shared singleton accessed via a global variable in each route module.

**Idempotency via job_id:** Every print request accepts an optional `job_id`. If the same `job_id` is submitted twice, the second request returns immediately without printing again. This prevents duplicate receipts in case of network retries.

**Failed job persistence:** When a print fails, the full job payload is written to `data/failed_jobs/{job_id}.json`. The `/reprint` endpoint reads this file and retries. After a successful reprint, the file is deleted.

**Two i18n systems:**
- `app/i18n/` — backend API error messages and status responses
- `ui/i18n/` — frontend JavaScript UI labels

Both must be kept in sync when adding new language keys.

### ESC/POS Command Reference

| Byte Sequence | Command | Effect |
|---------------|---------|--------|
| `ESC @` | Init | Reset printer |
| `ESC E 1` | Bold on | Enable bold |
| `ESC E 0` | Bold off | Disable bold |
| `ESC a 0/1/2` | Align | Left/Center/Right |
| `GS ! n` | Font size | Double width/height |
| `GS V 0` | Full cut | Cut paper |
| `GS V 1` | Partial cut | Partial paper cut |
| `GS ( k` | QR code | Print QR code |
| `GS v 0` | Raster image | Print bitmap |
| `LF` | Line feed | New line |

</details>

---

<a id="deutsch"></a>

<details>
<summary>🇩🇪 Deutsch — Klicken zum Aufklappen</summary>

## Deutsch

### Architekturübersicht

Der Backend besteht aus vier Schichten:

1. **API-Schicht** (`api/routes/`) — FastAPI-Endpunkte, HTTP-Request/Response-Handling
2. **Service-Schicht** (`services/`) — Geschäftslogik, Orchestrierung, Persistenz
3. **Core-Schicht** (`core/`) — ESC/POS-Engine, Druckerabstraktionen, Konfiguration
4. **Modell-Schicht** (`models/`) — Pydantic v2 Datenvalidierung

### Schlüsselkomponenten

**`escpos_engine.py`** — Wandelt strukturierte Druckaufträge in rohe ESC/POS-Bytes um, die direkt an den Drucker gesendet werden. Unterstützt Textformatierung, Bilder (via Pillow), QR-Codes und automatische Türkisch-Zeichencodierung (CP857).

**`print_service.py`** — Koordiniert den gesamten Druckablauf: Idempotenz-Prüfung → ESC/POS-Baytgenerierung → Druckerübertragung → Protokollierung → Fehlerbehandlung.

**`queue_service.py`** — In-Memory-Warteschlange mit asyncio.Queue. Fehlgeschlagene Jobs werden persistent auf der Festplatte gespeichert (`data/failed_jobs/`) für späteres Nachdrucken.

**`paper_service.py`** — Schätzt den Papierrollenverbrauch anhand der übertragenen Bytes und der durchschnittlichen Nutzung pro Ausdruck. Gibt Warnungen bei niedrigem Bestand aus.

</details>

---

<a id="français"></a>

<details>
<summary>🇫🇷 Français — Cliquer pour développer</summary>

## Français

### Vue d'ensemble de l'architecture

Le backend est organisé en quatre couches:

1. **Couche API** (`api/routes/`) — Endpoints FastAPI, gestion HTTP
2. **Couche Service** (`services/`) — Logique métier, orchestration, persistance
3. **Couche Core** (`core/`) — Moteur ESC/POS, abstractions imprimante, configuration
4. **Couche Modèle** (`models/`) — Validation des données Pydantic v2

### Composants clés

**`escpos_engine.py`** — Convertit les commandes d'impression structurées en bytes ESC/POS bruts. Supporte le formatage de texte, les images (via Pillow), les QR codes et l'encodage automatique des caractères turcs (CP857).

**`print_service.py`** — Orchestre le flux d'impression complet: vérification d'idempotence → génération ESC/POS → transmission → journalisation → gestion d'erreurs.

**`queue_service.py`** — File d'attente en mémoire avec asyncio.Queue. Les jobs échoués sont persistés sur disque (`data/failed_jobs/`) pour réimpression ultérieure.

**`paper_service.py`** — Estime la consommation du rouleau de papier en fonction des bytes transmis et de l'utilisation moyenne par impression.

</details>

---

← [Geri / Back to root README](../README.md)
