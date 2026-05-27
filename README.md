# Termal Yazıcı Servisi API

**Cashino KP-300 / KP-301H** termal yazıcılar için profesyonel REST API servisi. FastAPI (Python) ile geliştirilmiştir. USB ve LAN bağlantı desteği, tam ESC/POS komut yürütme, yapılandırılmış loglama, kuyruk yönetimi, çoklu dil desteği (TR/EN/DE/FR) ve opsiyonel yapay zeka entegrasyonu içerir.

---

## Quick Start

```bash
# 1. Clone and enter the project
git clone https://github.com/YOUR_USERNAME/thermal_printer_service.git
cd thermal_printer_service

# 2. Create virtual environment and install dependencies
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your printer settings

# 4. Run the service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 5. Open API docs (Modern Custom Design)
open http://localhost:8000/docs

# 6. Open Dashboard UI
open http://localhost:8000/ui
```

---

## Docker

```bash
# Build and start
docker compose up --build -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

### USB Printer with Docker

To pass a USB printer through to the Docker container, uncomment the `devices` section in `docker-compose.yml`:

```yaml
devices:
  - "/dev/bus/usb:/dev/bus/usb"
privileged: true
```

Find your device path with: `lsusb`

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `APP_HOST` | `0.0.0.0` | Server bind host |
| `APP_PORT` | `8000` | Server port |
| `APP_DEBUG` | `false` | Enable debug/reload mode |
| `API_BEARER_TOKEN` | `change-me-secret-token` | **Change this!** Bearer auth token |
| `DEFAULT_CONNECTION_TYPE` | `usb` | `usb` or `lan` |
| `USB_VENDOR_ID` | `0x0456` | Cashino KP-300 USB vendor ID |
| `USB_PRODUCT_ID` | `0x0808` | Cashino KP-300 USB product ID |
| `LAN_HOST` | `192.168.1.100` | Printer IP address |
| `LAN_PORT` | `9100` | Printer raw port (default 9100) |
| `RECONNECT_MAX_RETRIES` | `5` | Max auto-reconnect attempts |
| `RECONNECT_BACKOFF_BASE` | `2` | Exponential backoff base (seconds) |
| `RECONNECT_BACKOFF_MAX` | `60` | Max backoff delay (seconds) |
| `LOG_DIR` | `./logs` | Log file directory |
| `LOG_KEEP_DAYS` | `30` | Days to keep log files |
| `DEFAULT_LANGUAGE` | `en` | Default i18n language |
| `LLM_ENABLED` | `false` | Enable LLM feature (see below) |
| `OPENROUTER_API_KEY` | — | OpenRouter API key (only if LLM enabled) |
| `OPENROUTER_MODEL` | `mistralai/mistral-7b-instruct:free` | LLM model |

---

## API Reference

All endpoints except `GET /health` require a `Bearer` token:
```
Authorization: Bearer <your-token>
```

### Connection

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/connect` | Connect to printer via USB or LAN |
| `POST` | `/connect/disconnect` | Disconnect from printer |

**POST /connect — USB:**
```json
{ "connection_type": "usb" }
```

**POST /connect — LAN:**
```json
{ "connection_type": "lan", "lan_host": "192.168.1.100", "lan_port": 9100 }
```

### Print

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/print/text` | Print formatted text lines |
| `POST` | `/print/image` | Print base64-encoded PNG/JPEG image |
| `POST` | `/print/qr` | Print QR code with optional label |
| `POST` | `/print/smart` | LLM-assisted receipt from JSON data (optional) |
| `POST` | `/reprint` | Retry a failed job by job ID |

**POST /print/text example:**
```json
{
  "job_id": "receipt-001",
  "lines": [
    { "text": "ACO RECYCLING", "bold": true, "align": "center", "font_size": "double" },
    { "text": "Reward: 3.00 TL", "bold": true, "align": "center" },
    { "text": "Glass: 0  Plastic: 2  Metal: 1", "align": "left" }
  ],
  "cut": true
}
```

**POST /print/qr example:**
```json
{
  "data": "https://example.com",
  "size": 6,
  "error_correction": "M",
  "align": "center",
  "label": "Scan me!",
  "cut": true
}
```

**POST /print/image example:**
```json
{
  "image_base64": "<base64-encoded PNG/JPEG>",
  "align": "center",
  "cut": true
}
```

**POST /reprint:**
```json
{ "job_id": "receipt-001" }
```

### Status & Monitoring

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/status` | ✅ | Printer status, paper/cover/temp, queue size |
| `GET` | `/health` | ❌ | Service health (no auth — for Docker health checks) |
| `GET` | `/logs` | ✅ | Paginated JSON log entries |
| `GET` | `/logs/export` | ✅ | Download all logs as CSV |
| `GET` | `/logs/failed` | ✅ | List failed/pending reprint jobs |

**GET /logs query parameters:**
- `page` (default: 1)
- `page_size` (default: 100, max: 1000)
- `status` — filter: `done` | `failed` | `info`
- `op` — filter by operation name

---

## Error Codes

| Code | HTTP Status | KP-300 LED Flashes | Description |
|---|---|---|---|
| `PAPER_OUT` | 503 | 3 | No paper loaded |
| `PAPER_JAM` | 503 | 4 | Paper jam in cutter |
| `COVER_OPEN` | 503 | 6 | Printer cover/platen open |
| `OVERHEAT` | 503 | 5 | Print head overheating |
| `COMM_ERROR` | 502 | — | USB/LAN communication failure |
| `UNKNOWN_COMMAND` | 400 | — | Invalid ESC/POS command or request |

Error response format:
```json
{
  "detail": {
    "error": { "code": "PAPER_OUT", "detail": "Paper is out. Please load paper and retry." },
    "job_id": "receipt-001"
  }
}
```

---

## Log Schema

Every operation is logged in JSON Lines format (`logs/printer_service.jsonl`):

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

On failure:
```json
{
  "ts": "2025-09-16T16:20:00.000Z",
  "op": "print_text",
  "conn": "lan",
  "jobId": "receipt-002",
  "status": "failed",
  "error": { "code": "PAPER_OUT", "detail": "Paper is out. Please load paper and retry." }
}
```

---

## Internationalization (i18n)

All error messages and status responses support 4 languages. Set the language per-request:
```json
{ "lines": [...], "cut": true, "language": "tr" }
```

Or set the default globally via `DEFAULT_LANGUAGE=tr` in `.env`.

Supported: `en` (English), `tr` (Turkish), `de` (German), `fr` (French).

Translation files: `app/i18n/{lang}.json` — add new languages by adding a new JSON file.

---

## Reprint Queue

When a job fails, it is automatically saved to `data/failed_jobs/{job_id}.json`. To retry:

```bash
curl -X POST http://localhost:8000/reprint \
  -H "Authorization: Bearer change-me-secret-token" \
  -H "Content-Type: application/json" \
  -d '{"job_id": "receipt-001"}'
```

Failed jobs are deleted automatically after a successful reprint.

---

## Web UI Dashboard

A single-file dashboard is served at `http://localhost:8000/ui`. Features:
- Live printer status (auto-refreshes every 10 seconds)
- USB/LAN connection controls
- Print text, image, and QR code forms
- Log viewer with CSV export
- Failed job reprint interface
- Language switcher (EN / TR / DE / FR)
- Configurable API URL and Bearer token

### GitHub Pages Deployment

The UI is a static HTML file with no build step. Deploy to GitHub Pages:

```bash
# Option 1: Copy ui/ to docs/ branch
cp -r ui/ docs/
git add docs/
git commit -m "Add GitHub Pages UI"
git push

# Option 2: Use GitHub Actions (recommended)
# See .github/workflows/pages.yml
```

The UI will work in "demo mode" when hosted on GitHub Pages — you can still view the interface and configure it to point to your local service URL.

---

## LLM Integration (Optional Bonus Feature)

> **Task compliance note:** The task requirement states *"Dış servis/anahtar gerektiren ücretli SDK kullanmayınız (gerekirse açıkça not ediniz)"* — this LLM feature requires an external API key and is therefore **disabled by default**. The service is fully functional without it. This feature is explicitly documented here as required by the task rules.

When enabled, the `POST /print/smart` endpoint uses an LLM to convert arbitrary structured JSON data into a formatted receipt.

**Enable it:**
```env
LLM_ENABLED=true
OPENROUTER_API_KEY=sk-or-...
OPENROUTER_MODEL=mistralai/mistral-7b-instruct:free
```

**Example:**
```json
POST /print/smart
{
  "data": {
    "machine_id": "ACO-TEST-0001-0001",
    "reward": "3.00 TL",
    "plastic": 2,
    "metal": 1
  },
  "template_hint": "recycling reward receipt",
  "language": "tr"
}
```

The LLM generates receipt lines which are then printed via ESC/POS. If the LLM fails or is disabled, it falls back to a simple key-value format.

---

## Project Structure

```
thermal_printer_service/
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── api/
│   │   ├── deps.py              # Bearer auth dependency
│   │   └── routes/
│   │       ├── connection.py    # POST /connect, /disconnect
│   │       ├── print.py         # POST /print/*
│   │       ├── status.py        # GET /status
│   │       ├── logs.py          # GET /logs, /export, /failed
│   │       ├── health.py        # GET /health
│   │       └── reprint.py       # POST /reprint
│   ├── core/
│   │   ├── config.py            # pydantic-settings configuration
│   │   ├── escpos_engine.py     # ESC/POS command builder
│   │   ├── printer.py           # Abstract base + factory
│   │   ├── usb_printer.py       # USB backend (pyusb)
│   │   ├── lan_printer.py       # LAN backend (asyncio TCP)
│   │   └── error_handler.py     # Error codes + PrinterError
│   ├── models/
│   │   ├── requests.py          # Pydantic request models
│   │   └── responses.py         # Pydantic response models
│   ├── services/
│   │   ├── print_service.py     # Print orchestration
│   │   ├── log_service.py       # JSON/CSV logging
│   │   ├── queue_service.py     # Job queue + failed job store
│   │   ├── i18n_service.py      # Internationalization
│   │   └── llm_service.py       # Optional OpenRouter LLM
│   └── i18n/
│       ├── en.json              # English translations
│       ├── tr.json              # Turkish translations
│       ├── de.json              # German translations
│       └── fr.json              # French translations
├── ui/
│   └── index.html               # Dashboard UI (also deployable to GitHub Pages)
├── tests/
│   ├── conftest.py              # pytest fixtures
│   ├── mock_printer.py          # Hardware-free mock printer
│   ├── test_api.py              # API endpoint tests
│   ├── test_escpos.py           # ESC/POS unit tests
│   └── test_services.py         # Service layer unit tests
├── logs/                        # Runtime log files (gitignored)
├── data/failed_jobs/            # Failed job persistence (gitignored)
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── requirements.txt
├── pytest.ini
├── .env.example
└── README.md
```

---

## Running Tests

```bash
pip install -r requirements.txt
pytest -v
```

Expected output: all tests pass (no physical printer required — tests use a mock).

---

## Printer Hardware Notes

- **Cashino KP-300**: 80mm paper, 203dpi, 250mm/s, USB Type B + RJ45 + RS232
- **Cashino KP-301H**: 25-83mm adjustable paper, 203dpi, 250mm/s, USB + RJ45 + RS232
- **Default USB IDs**: VID `0x0456`, PID `0x0808` (set in `.env` if yours differ — check with `lsusb`)
- **Default LAN port**: `9100` (RAW printing standard port)
- **Paper width**: 80mm model uses 576px max raster image width at 203dpi

### LED Error Indicators (KP-301H)

| Flash Count | Error |
|---|---|
| 2 | Print head not connected |
| 3 | No paper (PAPER_OUT) |
| 4 | Cutter error (PAPER_JAM) |
| 5 | Overheat (OVERHEAT) |
| 6 | Platen open (COVER_OPEN) |

---

## License

MIT License — free for personal and commercial use.
