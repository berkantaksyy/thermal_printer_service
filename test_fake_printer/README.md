# 🖨️ test_fake_printer/ — TCP Sahte Yazıcı Simülatörü

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python)](https://python.org)
[![TCP](https://img.shields.io/badge/TCP-Port%209100-orange?style=flat-square)](.)
[![ESC/POS](https://img.shields.io/badge/ESC%2FPOS-Parsed-green?style=flat-square)](.)

[🇹🇷 Türkçe](#türkçe) · [🇬🇧 English](#english) · [🇩🇪 Deutsch](#deutsch) · [🇫🇷 Français](#français)

</div>

---

<a id="türkçe"></a>

## 🇹🇷 Türkçe

### Nedir?

`fake_printer.py`, fiziksel Cashino KP-300/KP-301H yazıcısı olmadan API servisini test etmek için geliştirilmiş bir TCP sunucusudur. Port 9100'de dinler ve gerçek termal yazıcı gibi davranır.

Gerçek yazıcı olmadan:
- API entegrasyon testleri yapabilirsiniz
- ESC/POS komutlarını terminal çıktısı olarak görebilirsiniz
- Hata senaryolarını simüle edebilirsiniz

### Hızlı Başlangıç

```bash
cd test_fake_printer

# Temel mod (sadece TCP sunucu)
python3 fake_printer.py

# ESC/POS komutlarını göster
python3 fake_printer.py --mode parse

# Tam simülasyon (hata senaryoları dahil)
python3 fake_printer.py --mode simulate

# Tüm testleri otomatik çalıştır
./run_all_tests.sh

# Hızlı kurulum (servis + fake yazıcı)
./quick_start.sh
```

### Çalışma Modları

#### `--mode simple` (varsayılan)
Gelen bağlantıları kabul eder ve veriyi yoksayar. Sadece bağlantı testleri için.

```
[FAKE PRINTER] Listening on 127.0.0.1:9100
[FAKE PRINTER] Client connected: ('127.0.0.1', 54321)
[FAKE PRINTER] Received 42 bytes
[FAKE PRINTER] Client disconnected
```

#### `--mode parse`
Gelen ESC/POS baytlarını ayrıştırır ve insan okunabilir formatta terminale yazar.

```
[FAKE PRINTER] Listening on 127.0.0.1:9100
[FAKE PRINTER] Client connected
[PARSER] INIT: ESC @
[PARSER] ALIGN: Center (ESC a 1)
[PARSER] BOLD ON: ESC E 1
[PARSER] TEXT: "ACO RECYCLING"
[PARSER] BOLD OFF: ESC E 0
[PARSER] TEXT: "Makinesi: ACO-TEST-0001"
[PARSER] QR CODE: data="https://aco.example.com/r/12345", size=6
[PARSER] CUT: Full cut (GS V 0)
```

#### `--mode simulate`
Gerçek yazıcı davranışını simüle eder. Özel komutlar ile 6 farklı hata senaryosu tetiklenebilir.

### Hata Simülasyonu

`simulate` modunda aşağıdaki özel komutlar TCP üzerinden gönderilebilir:

| Komut | Açıklama |
|-------|----------|
| `SIMULATE_PAPER_OUT` | Kağıt bitti hatası tetikle |
| `SIMULATE_PAPER_JAM` | Kağıt sıkışması hatası tetikle |
| `SIMULATE_COVER_OPEN` | Kapak açık hatası tetikle |
| `SIMULATE_OVERHEAT` | Aşırı ısınma hatası tetikle |
| `SIMULATE_COMM_ERROR` | İletişim hatası tetikle |
| `SIMULATE_CLEAR` | Tüm hataları temizle, normal çalışmaya dön |

**Örnek kullanım:**
```bash
# Simülatörü başlat
python3 fake_printer.py --mode simulate

# Farklı terminalde hata tetikle
echo -n "SIMULATE_PAPER_OUT" | nc 127.0.0.1 9100

# API'ye yazdırma isteği gönder → 503 alacaksınız
curl -X POST http://localhost:8000/print/text \
  -H "Authorization: Bearer change-me-secret-token" \
  -H "Content-Type: application/json" \
  -d '{"lines": [{"text": "Test"}], "cut": true}'

# Hatayı temizle
echo -n "SIMULATE_CLEAR" | nc 127.0.0.1 9100

# Tekrar dene → başarılı
```

### Komut Satırı Seçenekleri

```
python3 fake_printer.py [seçenekler]

  --host HOST       Dinleme adresi (varsayılan: 127.0.0.1)
  --port PORT       Dinleme portu  (varsayılan: 9100)
  --mode MODE       Çalışma modu: simple | parse | simulate  (varsayılan: simple)
  --delay SECS      Her yanıt için gecikme (yavaş yazıcı simülasyonu)
  --verbose         Detaylı çıktı
```

### Tam Entegrasyon Test Akışı (3 Terminal)

**Terminal 1 — Sahte Yazıcı:**
```bash
cd test_fake_printer
python3 fake_printer.py --mode parse
```

**Terminal 2 — API Servisi:**
```bash
cat > .env << EOF
DEFAULT_CONNECTION_TYPE=lan
LAN_HOST=127.0.0.1
LAN_PORT=9100
API_BEARER_TOKEN=change-me-secret-token
EOF

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**Terminal 3 — Test İstekleri:**
```bash
# Bağlan
curl -X POST http://localhost:8000/connect \
  -H "Authorization: Bearer change-me-secret-token" \
  -H "Content-Type: application/json" \
  -d '{"connection_type": "lan"}'

# Metin yazdır
curl -X POST http://localhost:8000/print/text \
  -H "Authorization: Bearer change-me-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "lines": [
      {"text": "TEST", "bold": true, "align": "center"},
      {"text": "Merhaba Dünya!"}
    ],
    "cut": true
  }'

# QR kod yazdır
curl -X POST http://localhost:8000/print/qr \
  -H "Authorization: Bearer change-me-secret-token" \
  -H "Content-Type: application/json" \
  -d '{"data": "https://github.com/berkantaksyy", "size": 6, "cut": true}'
```

### `run_all_tests.sh` — Otomatik Test Scripti

```bash
./run_all_tests.sh
# ✅ Health check
# ✅ Print text
# ✅ Print QR code
# ✅ Print image
# ✅ Get status
# ✅ Get logs
# ✅ Error simulation (PAPER_OUT → 503)
# ✅ Error recovery (SIMULATE_CLEAR → 200)
# ✅ Idempotency (duplicate job_id)
# ✅ Reprint (failed job)
```

### `quick_start.sh` — Tek Komut Kurulum

```bash
./quick_start.sh
# ① Gereksinimler kontrol edilir (Python, curl, nc)
# ② .env dosyası oluşturulur
# ③ Sahte yazıcı arka planda başlatılır (port 9100)
# ④ API servisi başlatılır (port 8000)
# ⑤ Bağlantı testi yapılır
# ⑥ Örnek yazdırma isteği gönderilir
```

### Fark: `mock_printer.py` vs `fake_printer.py`

| | `mock_printer.py` (`tests/`) | `fake_printer.py` |
|---|---|---|
| **Kullanım amacı** | pytest otomatik testleri | Manuel entegrasyon testi |
| **Protokol** | Direkt Python metod çağrısı | Gerçek TCP/IP ağ soketi |
| **ESC/POS ayrıştırma** | Hayır | Evet (`parse` modunda) |
| **Hata tetikleme** | `printer.simulate_error()` | TCP üzerinden string gönder |
| **CI uyumluluğu** | ✅ Tam uyumlu | ⚠️ Manuel başlatma gerekir |
| **Gerçekçilik** | Orta | Yüksek (gerçek ağ soketi) |

---

<a id="english"></a>

<details>
<summary>🇬🇧 English — Click to expand</summary>

## English

### What is it?

`fake_printer.py` is a TCP server that simulates a Cashino KP-300/KP-301H thermal printer. It listens on port 9100 so the API service connects to it exactly as it would to a real printer.

Use it to:
- Test the full API integration flow without hardware
- Inspect ESC/POS commands in human-readable form (`--mode parse`)
- Simulate all 6 printer error scenarios (`--mode simulate`)

### Quick Start

```bash
cd test_fake_printer
python3 fake_printer.py --mode parse     # Show ESC/POS commands
./run_all_tests.sh                       # Run all automated tests
./quick_start.sh                         # Full setup in one command
```

### Modes

| Mode | Description |
|------|-------------|
| `simple` | Accept TCP connections, ignore data |
| `parse` | Parse ESC/POS bytes → human-readable terminal output |
| `simulate` | Full simulation with 6 error scenarios |

### Error Simulation (`--mode simulate`)

Send these strings over TCP to trigger errors:

| Trigger | Error |
|---------|-------|
| `SIMULATE_PAPER_OUT` | Paper roll empty |
| `SIMULATE_PAPER_JAM` | Paper jam |
| `SIMULATE_COVER_OPEN` | Cover open |
| `SIMULATE_OVERHEAT` | Overheating |
| `SIMULATE_COMM_ERROR` | Communication failure |
| `SIMULATE_CLEAR` | Clear all errors, resume normal operation |

### Integration Test Flow (3 Terminals)

```bash
# Terminal 1: Start fake printer
cd test_fake_printer && python3 fake_printer.py --mode parse

# Terminal 2: Configure API for LAN connection
cat > ../.env << EOF
DEFAULT_CONNECTION_TYPE=lan
LAN_HOST=127.0.0.1
LAN_PORT=9100
API_BEARER_TOKEN=change-me-secret-token
EOF
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 3: Connect and send test requests
curl -X POST http://localhost:8000/connect \
  -H "Authorization: Bearer change-me-secret-token" \
  -H "Content-Type: application/json" \
  -d '{"connection_type": "lan"}'

curl -X POST http://localhost:8000/print/text \
  -H "Authorization: Bearer change-me-secret-token" \
  -H "Content-Type: application/json" \
  -d '{"lines": [{"text": "Hello!", "bold": true, "align": "center"}], "cut": true}'
```

### Difference from pytest Mock Printer

| | `tests/mock_printer.py` | `fake_printer.py` |
|---|---|---|
| **Used by** | Automated pytest suite | Manual integration testing |
| **Protocol** | Direct Python method calls | Real TCP/IP socket |
| **ESC/POS parsing** | No | Yes (parse mode) |
| **Error triggering** | `printer.simulate_error()` | Send string over TCP |
| **CI compatible** | ✅ Yes | ⚠️ Requires manual start |

</details>

---

<a id="deutsch"></a>

<details>
<summary>🇩🇪 Deutsch — Klicken zum Aufklappen</summary>

## Deutsch

### Was ist das?

`fake_printer.py` ist ein TCP-Server, der einen Cashino KP-300/KP-301H Thermodrucker simuliert. Er lauscht auf Port 9100 für echte Netzwerktests ohne Hardware.

### Schnellstart

```bash
cd test_fake_printer
python3 fake_printer.py --mode parse    # ESC/POS-Befehle anzeigen
./run_all_tests.sh                      # Automatisierte Tests ausführen
./quick_start.sh                        # Vollständige Einrichtung
```

### Modi

| Modus | Beschreibung |
|-------|--------------|
| `simple` | TCP-Verbindungen akzeptieren, Daten ignorieren |
| `parse` | ESC/POS-Bytes parsen → lesbarer Terminal-Output |
| `simulate` | Vollständige Simulation mit 6 Fehlerszenarien |

### Fehlersimulation (`--mode simulate`)

| Trigger | Fehler |
|---------|--------|
| `SIMULATE_PAPER_OUT` | Papier leer |
| `SIMULATE_PAPER_JAM` | Papierstau |
| `SIMULATE_COVER_OPEN` | Abdeckung offen |
| `SIMULATE_OVERHEAT` | Überhitzung |
| `SIMULATE_COMM_ERROR` | Kommunikationsfehler |
| `SIMULATE_CLEAR` | Alle Fehler löschen |

### Integrationstest-Ablauf (3 Terminals)

```bash
# Terminal 1: Fake-Drucker starten
python3 fake_printer.py --mode parse

# Terminal 2: API konfigurieren und starten
DEFAULT_CONNECTION_TYPE=lan LAN_HOST=127.0.0.1 LAN_PORT=9100 \
  python -m uvicorn app.main:app --port 8000

# Terminal 3: Testen
curl -X POST http://localhost:8000/connect \
  -H "Authorization: Bearer change-me-secret-token" \
  -d '{"connection_type": "lan"}' -H "Content-Type: application/json"
```

</details>

---

<a id="français"></a>

<details>
<summary>🇫🇷 Français — Cliquer pour développer</summary>

## Français

### Qu'est-ce que c'est?

`fake_printer.py` est un serveur TCP qui simule une imprimante thermique Cashino KP-300/KP-301H sur le port 9100 pour des tests réseau réels sans matériel.

### Démarrage rapide

```bash
cd test_fake_printer
python3 fake_printer.py --mode parse    # Afficher les commandes ESC/POS
./run_all_tests.sh                      # Tests automatisés
./quick_start.sh                        # Configuration complète
```

### Modes

| Mode | Description |
|------|-------------|
| `simple` | Accepter les connexions TCP, ignorer les données |
| `parse` | Analyser les bytes ESC/POS → sortie lisible |
| `simulate` | Simulation complète avec 6 scénarios d'erreur |

### Simulation d'erreurs (`--mode simulate`)

| Déclencheur | Erreur |
|-------------|--------|
| `SIMULATE_PAPER_OUT` | Rouleau vide |
| `SIMULATE_PAPER_JAM` | Bourrage papier |
| `SIMULATE_COVER_OPEN` | Couvercle ouvert |
| `SIMULATE_OVERHEAT` | Surchauffe |
| `SIMULATE_COMM_ERROR` | Erreur de communication |
| `SIMULATE_CLEAR` | Effacer toutes les erreurs |

### Flux de test d'intégration (3 terminaux)

```bash
# Terminal 1: Démarrer la fausse imprimante
python3 fake_printer.py --mode parse

# Terminal 2: Configurer et démarrer l'API
DEFAULT_CONNECTION_TYPE=lan LAN_HOST=127.0.0.1 LAN_PORT=9100 \
  python -m uvicorn app.main:app --port 8000

# Terminal 3: Tester
curl -X POST http://localhost:8000/connect \
  -H "Authorization: Bearer change-me-secret-token" \
  -d '{"connection_type": "lan"}' -H "Content-Type: application/json"
```

</details>

---

← [Geri / Back to root README](../README.md)
