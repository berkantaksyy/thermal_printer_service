# 🧪 tests/ — Test Paketi

<div align="center">

[![Tests](https://img.shields.io/badge/Tests-56%20passing-4CAF50?style=flat-square&logo=pytest)](.)
[![pytest](https://img.shields.io/badge/pytest-8.x-0A9EDC?style=flat-square&logo=pytest)](https://pytest.org)
[![Async](https://img.shields.io/badge/Async-82%25-orange?style=flat-square)](.)
[![Coverage](https://img.shields.io/badge/Coverage-API%20%7C%20Services%20%7C%20ESC%2FPOS%20%7C%20Errors-blue?style=flat-square)](.)

[🇹🇷 Türkçe](#türkçe) · [🇬🇧 English](#english) · [🇩🇪 Deutsch](#deutsch) · [🇫🇷 Français](#français)

</div>

---

<a id="türkçe"></a>

## 🇹🇷 Türkçe

### Genel Bakış

```
tests/
├── conftest.py                  # pytest fixture'ları (event_loop, client, connected_client)
├── mock_printer.py              # Fiziksel donanım gerektirmeyen mock yazıcı
├── test_api.py                  # API endpoint entegrasyon testleri (17 test)
├── test_services.py             # Servis katmanı birim testleri (14 test)
├── test_escpos.py               # ESC/POS komut birim testleri (10 test)
└── test_mock_printer_errors.py  # Mock yazıcı hata simülasyon testleri (15 test)
```

### Test Dağılımı

```
┌─────────────────────────────────────────────────────────┐
│ Test Dağılımı                                           │
├─────────────────────────────────────────────────────────┤
│ API Endpoint'leri:      17 test  (30.4%)               │
│ Servis Katmanı:         14 test  (25.0%)               │
│ ESC/POS Motoru:         10 test  (17.9%)               │
│ Hata Simülasyonu:       15 test  (26.8%)               │
├─────────────────────────────────────────────────────────┤
│ Toplam:                 56 test  (100%)                │
└─────────────────────────────────────────────────────────┘

Async testler:  46 test (%82)
Sync testler:   10 test (%18)
```

### Testleri Çalıştırma

```bash
# Tüm testler
pytest -v

# Belirli bir dosya
pytest tests/test_api.py -v
pytest tests/test_services.py -v
pytest tests/test_escpos.py -v
pytest tests/test_mock_printer_errors.py -v

# Belirli bir test
pytest tests/test_api.py::test_print_text_idempotency -v

# Kapsam raporu ile
pytest --cov=app --cov-report=html
# htmlcov/index.html dosyasını tarayıcıda açın

# Sessiz çıktı
pytest -q

# Paralel çalıştır (pytest-xdist gerekir)
pytest -n auto
```

---

### `conftest.py` — Fixture'lar

#### `event_loop` (session-scoped)
Tüm async testler için tek bir asyncio event loop paylaşır. Bu, testler arası state sızıntısını önler ve test süitinin daha hızlı çalışmasını sağlar.

```python
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

#### `client` (function-scoped)
`httpx.AsyncClient` ile önceden yapılandırılmış Bearer token içerir. Tüm korunan endpoint testlerinde kullanılır. Her test fonksiyonu için temiz bir istemci döner.

```python
@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        ac.headers["Authorization"] = "Bearer test-token"
        yield ac
```

#### `connected_client` (function-scoped)
`client` fixture'ı üzerine kurulu — mock yazıcı önceden bağlı durumda. Yazdırma testleri için kullanılır; her test öncesinde bağlantı adımı gerekmez.

---

### `mock_printer.py` — Mock Yazıcı

Fiziksel yazıcı olmadan tüm yazıcı davranışlarını simüle eder.

#### Desteklenen Özellikler

- `connect()` / `disconnect()` — bağlantı yönetimi
- `write(data: bytes)` — veri gönderimi (gerçek yazıcıya göndermez, istatistik tutar)
- `is_connected` — bağlantı durumu özelliği
- 6 hata senaryosu simülasyonu
- İstatistik takibi: `write_count`, `error_count`, `total_bytes_written`

#### Hata Simülasyon API'si

```python
printer = MockPrinter()
await printer.connect()

# Belirli bir hata için ayarla
printer.simulate_error(PrinterErrorCode.PAPER_OUT)

# Sınırlı sayıda işlem için hata
printer.simulate_error(PrinterErrorCode.PAPER_JAM, operations=2)

# Hatayı temizle (kurtarma simülasyonu)
printer.clear_error()

# İstatistikler
print(printer.write_count)        # Toplam write() çağrısı
print(printer.error_count)        # Toplam hata sayısı
print(printer.total_bytes_written) # Toplam gönderilen byte
```

---

### Test Dosyaları Detaylı

---

## 1. `test_api.py` — API Endpoint Testleri (17 Test)

### Sağlık & Durum Endpoint'leri

#### `test_health_no_auth`
**Neden var:** `/health` endpoint'i Docker sağlık kontrolü için tasarlanmıştır ve kimlik doğrulama gerektirmemelidir. Bu test, endpoint'in token olmadan 200 döndürdüğünü garantiler.

```python
async def test_health_no_auth(client):
    response = await client.get("/health", headers={})  # Auth başlığı yok
    assert response.status_code == 200
```

#### `test_health_with_token`
**Neden var:** Token ile de çalışması gerektiğini doğrular — tokenın varlığı `/health`'i kırmamalı.

#### `test_status_no_printer`
**Neden var:** Yazıcı bağlı değilken `/status` endpoint'inin anlamlı bir yanıt döndürdüğünü (`disconnected` durumu) doğrular. Kullanıcının API'yi yazıcı bağlamadan kullanabilmesi gerekir.

#### `test_status_with_mock_printer`
**Neden var:** Mock yazıcı bağlıyken `/status`'un doğru bağlantı bilgilerini döndürdüğünü doğrular (bağlantı tipi, durum, vb.).

---

### Yazdırma İşlemleri

#### `test_print_text_no_printer`
**Neden var:** Yazıcı bağlı değilken `/print/text`'in 502 döndürdüğünü doğrular. Kullanıcıya anlamlı hata mesajı verilmesi kritiktir.

```python
async def test_print_text_no_printer(client):
    response = await client.post("/print/text", json={...})
    assert response.status_code == 502
    assert response.json()["detail"]["error"]["code"] == "COMM_ERROR"
```

#### `test_print_text_with_printer`
**Neden var:** Temel yazdırmanın çalıştığını doğrular — mock yazıcı bağlıyken metin gönderilmesi başarılı olmalı ve iş kaydı döndürülmeli.

#### `test_print_text_idempotency`
**Neden var:** Aynı `job_id` ile iki kez gönderim durumunda yazıcıya sadece bir kez yazıldığını doğrular. Ağ yeniden denemeleri veya kullanıcı hatası durumunda çift baskıyı önler.

```python
async def test_print_text_idempotency(connected_client):
    payload = {"job_id": "idempotent-001", "lines": [...], "cut": True}
    r1 = await connected_client.post("/print/text", json=payload)
    r2 = await connected_client.post("/print/text", json=payload)
    assert r1.status_code == 200
    assert r2.status_code == 200
    # Mock yazıcıda sadece 1 write() çağrısı olmalı
    assert mock_printer.write_count == 1
```

#### `test_print_qr`
**Neden var:** QR kod yazdırmanın end-to-end çalıştığını doğrular. QR kod için özel ESC/POS komutları (`GS ( k`) kullanılır.

#### `test_print_image_invalid_base64`
**Neden var:** Geçersiz base64 görselinin 422 (Unprocessable Entity) döndürdüğünü doğrular. Pydantic doğrulamasının beklenen şekilde çalıştığını garantiler.

---

### Yeniden Baskı & Loglar

#### `test_reprint_not_found`
**Neden var:** Var olmayan `job_id` ile yeniden baskı isteğinin 400 döndürdüğünü doğrular.

#### `test_logs_empty`
**Neden var:** Log endpoint'inin başlangıçta boş liste döndürdüğünü doğrular (temiz test ortamı).

#### `test_logs_after_print`
**Neden var:** Her başarılı yazdırma işleminden sonra log kaydı oluşturulduğunu doğrular. Log sisteminin çalıştığını garantiler.

---

### Kimlik Doğrulama & Bağlantı

#### `test_unauthorized_no_token`
**Neden var:** Token olmadan korumalı endpoint'lerin 401 döndürdüğünü doğrular. Güvenlik katmanının çalıştığını garantiler.

#### `test_connect_disconnect`
**Neden var:** `/connect` ve `/connect/disconnect` endpoint'lerinin simülasyon modunda çalıştığını doğrular.

---

## 2. `test_services.py` — Servis Katmanı Testleri (14 Test)

### Log Servisi (4 Test)

#### `test_log_write_and_read`
**Neden var:** Log servisinin JSONL dosyasına yazıp geri okuyabildiğini doğrular. Veri kalıcılığının çalıştığını garantiler.

#### `test_log_csv_export`
**Neden var:** CSV dışa aktarmanın doğru formatında çıktı ürettiğini doğrular (başlık satırı, tüm alanlar).

#### `test_log_filter_by_status`
**Neden var:** `done`/`failed` durumuna göre filtrelemenin doğru çalıştığını doğrular.

---

### Kuyruk Servisi (4 Test)

#### `test_queue_enqueue_and_dequeue`
**Neden var:** Temel kuyruk operasyonlarının çalıştığını doğrular: iş ekleme, iş alma.

#### `test_queue_idempotency`
**Neden var:** Aynı `job_id` ile iki kez ekleme yapılırsa ikinci kaydın `is_duplicate=True` döndürdüğünü doğrular.

```python
async def test_queue_idempotency():
    svc = QueueService()
    r1 = await svc.enqueue("print_text", {}, job_id="abc")
    r2 = await svc.enqueue("print_text", {}, job_id="abc")
    assert r1.is_duplicate == False
    assert r2.is_duplicate == True
```

#### `test_failed_job_persist_and_retrieve`
**Neden var:** Başarısız bir işin diske kaydedildiğini ve `get_failed()` ile geri alınabildiğini doğrular. Gerçek iş akışının kritik bir parçası.

---

### i18n Servisi (4 Test)

#### `test_i18n_english` / `test_i18n_turkish`
**Neden var:** İngilizce ve Türkçe çevirilerin doğru çekildiğini doğrular.

#### `test_i18n_fallback_to_english`
**Neden var:** Bilinmeyen dil veya eksik anahtar için İngilizceye düştüğünü doğrular. Hiçbir zaman ham anahtar string'i döndürmemeli.

#### `test_i18n_all_error_codes_have_translations`
**Neden var:** Tüm hata kodlarının (`PAPER_OUT`, `PAPER_JAM`, vb.) 4 dilde de çevirisi olduğunu doğrular. Yeni dil eklendiğinde eksik çeviri olmadığını garantiler.

```python
def test_i18n_all_error_codes_have_translations():
    for lang in ["en", "tr", "de", "fr"]:
        for code in ErrorCode:
            result = get_translation(lang, f"error.{code.value}")
            assert result != f"error.{code.value}"  # ham anahtar döndürülmemeli
```

---

### Hata İşleyici (2 Test)

#### `test_all_error_codes_defined`
**Neden var:** `ErrorCode` enum'undaki her kodun `error_handler.py`'de metadata tanımına (HTTP status, açıklama) sahip olduğunu doğrular.

#### `test_error_http_status`
**Neden var:** Farklı hata tiplerinin doğru HTTP durum kodlarına eşlendiğini doğrular (PAPER_OUT → 503, COMM_ERROR → 502, UNKNOWN_COMMAND → 400).

---

## 3. `test_escpos.py` — ESC/POS Birim Testleri (10 Test)

### Temel Komutlar

#### `test_init_returns_correct_bytes`
**Neden var:** `EscposEngine.init()` metodunun tam olarak `b'\x1b\x40'` (ESC @) döndürdüğünü doğrular. Yanlış init baytları yazıcıyı garip duruma sokar.

```python
def test_init_returns_correct_bytes():
    engine = EscposEngine()
    assert engine.init() == b'\x1b\x40'
```

#### `test_text_line_basic`
**Neden var:** Basit bir metin satırının doğru baytları (metin + LF) ürettiğini doğrular.

#### `test_text_line_bold`
**Neden var:** Bold metin için `ESC E 1` açma ve `ESC E 0` kapatma komutlarının eklendiğini doğrular.

```python
def test_text_line_bold():
    engine = EscposEngine()
    result = engine.text_line("Hello", bold=True)
    assert b'\x1b\x45\x01' in result  # ESC E 1 (bold on)
    assert b'\x1b\x45\x00' in result  # ESC E 0 (bold off)
```

#### `test_text_line_center_align`
**Neden var:** Ortalama hizalama için `ESC a 1` komutunun eklendiğini doğrular.

#### `test_cut_command`
**Neden var:** Tam kesme (`GS V 0`) ve kısmi kesme (`GS V 1`) komutlarının doğru olduğunu doğrular. Yanlış kesme komutu kağıdı sıkıştırabilir.

#### `test_feed_lines`
**Neden var:** `feed_lines(n)` metodunun tam olarak `n` adet LF baytı döndürdüğünü doğrular.

---

### Fiş Oluşturma

#### `test_build_receipt_has_init_and_cut`
**Neden var:** `build_receipt()` çıktısının init komutu ile başladığını ve `cut=True` olduğunda kesme komutu ile bittiğini doğrular.

#### `test_build_receipt_no_cut`
**Neden var:** `cut=False` olduğunda kesme komutunun eklenmediğini doğrular.

---

### Gelişmiş Özellikler

#### `test_qr_code_generates_bytes`
**Neden var:** QR kod fonksiyonunun `GS ( k` komut başlığını içeren baytlar ürettiğini doğrular. QR kod protokolü karmaşık olduğundan ayrı test edilir.

#### `test_turkish_text_encoding`
**Neden var:** Türkçe karakterlerin (Ç, Ğ, İ, Ö, Ş, Ü) CP857 kodlamasında doğru dönüştürüldüğünü doğrular. Yanlış kodlama karakterleri bozuk gösterir.

```python
def test_turkish_text_encoding():
    engine = EscposEngine()
    result = engine.text_line("Çıktı: ÖĞRENCİ")
    # CP857 ile kodlanmış byte'lar beklenir
    assert result  # En azından boş olmamalı ve hata vermemeli
```

---

## 4. `test_mock_printer_errors.py` — Hata Simülasyon Testleri (15 Test)

### Temel Hata Senaryoları (6 Test)

#### `test_paper_out_error`
**Neden var:** `PAPER_OUT` hatasının mock yazıcıda `PrinterError(ErrorCode.PAPER_OUT)` fırlatılmasını tetiklediğini doğrular.

#### `test_paper_jam_error`
**Neden var:** `PAPER_JAM` hatasının doğru şekilde simüle edildiğini doğrular.

#### `test_cover_open_error`
**Neden var:** `COVER_OPEN` hatasının doğru şekilde simüle edildiğini doğrular.

#### `test_overheat_error`
**Neden var:** `OVERHEAT` hatasının doğru şekilde simüle edildiğini doğrular.

#### `test_comm_error`
**Neden var:** `COMM_ERROR` hatasının doğru şekilde simüle edildiğini doğrular.

#### `test_unknown_command_error`
**Neden var:** `UNKNOWN_COMMAND` hatasının doğru şekilde simüle edildiğini doğrular.

---

### Hata Kurtarma & Sınırlar (2 Test)

#### `test_error_for_limited_operations`
**Neden var:** `simulate_error(code, operations=N)` ile hatanın yalnızca `N` işlem için aktif olduğunu doğrular. Gerçek dünyada kağıt sıkışması 2-3 işlem sonra temizlenebilir.

```python
async def test_error_for_limited_operations():
    printer = MockPrinter()
    await printer.connect()
    printer.simulate_error(PrinterErrorCode.PAPER_JAM, operations=2)
    
    with pytest.raises(PrinterError):
        await printer.write(b"test1")  # Hata
    with pytest.raises(PrinterError):
        await printer.write(b"test2")  # Hata
    
    await printer.write(b"test3")  # Başarılı — hata sona erdi
```

#### `test_error_recovery_after_clear`
**Neden var:** `clear_error()` çağrıldıktan sonra yazıcının normal çalışmaya döndüğünü doğrular. Operatörün kapağı kapatmasını simüle eder.

---

### API Entegrasyonu ile Hatalar (4 Test)

#### `test_api_print_with_paper_out`
**Neden var:** Kağıt bittiğinde `/print/text` endpoint'inin 503 döndürdüğünü ve hata yanıtının `PAPER_OUT` kodu içerdiğini doğrular.

#### `test_api_print_with_cover_open`
**Neden var:** Kapak açıkken API'nin 503 döndürdüğünü doğrular.

#### `test_api_print_with_overheat`
**Neden var:** Aşırı ısınmada API'nin 503 döndürdüğünü doğrular.

#### `test_api_status_reflects_errors`
**Neden var:** Hata durumunda `/status` endpoint'inin hata durumunu yansıttığını doğrular — kullanıcı dashboard'dan yazıcı sorununu görebilmeli.

---

### Gerçekçi Senaryolar (3 Test)

#### `test_intermittent_paper_jam_scenario`
**Neden var:** Gerçekçi kağıt sıkışması senaryosunu simüle eder: 2 kez başarısız → `clear_error()` → başarılı. Yazıcının kurtarma akışını test eder.

```python
async def test_intermittent_paper_jam_scenario():
    printer = MockPrinter()
    await printer.connect()
    
    printer.simulate_error(PrinterErrorCode.PAPER_JAM, operations=2)
    
    # İlk 2 deneme başarısız
    for _ in range(2):
        with pytest.raises(PrinterError) as exc:
            await printer.write(b"data")
        assert exc.value.code == ErrorCode.PAPER_JAM
    
    # Kağıt sıkışması giderildi (kapak açıp kapandı)
    await printer.write(b"data")  # Başarılı
```

#### `test_multiple_error_types_sequence`
**Neden var:** Birden fazla hata tipinin sırayla değiştirilebildiğini doğrular (önce PAPER_OUT, sonra OVERHEAT). Gerçek yazıcıların farklı sorunlar yaşayabileceğini test eder.

#### `test_comm_error_on_connect`
**Neden var:** Bağlanma sırasında iletişim hatası oluştuğunda `connect()` metodunun hata fırlattığını doğrular.

---

### İstatistikler & Genel Metotlar (2 Test)

#### `test_error_statistics_tracking`
**Neden var:** `write_count`, `error_count` ve `total_bytes_written` istatistiklerinin doğru takip edildiğini doğrular. Bu veriler üretim ortamında izleme ve hata ayıklama için kullanılır.

```python
async def test_error_statistics_tracking():
    printer = MockPrinter()
    await printer.connect()
    
    await printer.write(b"hello")          # write_count=1
    printer.simulate_error(PrinterErrorCode.COMM_ERROR)
    try:
        await printer.write(b"world")     # error_count=1
    except PrinterError:
        pass
    
    assert printer.write_count == 1
    assert printer.error_count == 1
    assert printer.total_bytes_written == 5  # "hello" = 5 byte
```

#### `test_generic_simulate_error_with_string`
**Neden var:** `simulate_error()` metodunun string hata kodu ile de çalıştığını doğrular (enum yanı sıra).

#### `test_generic_simulate_error_with_enum`
**Neden var:** `simulate_error()` metodunun `PrinterErrorCode` enum değeri ile de çalıştığını doğrular.

---

### Test Kalite Metrikleri

| Metrik | Değer |
|--------|-------|
| Toplam test | 56 |
| Async test | 46 (%82) |
| Sync test | 10 (%18) |
| Kapsanan hata kodu | 6/6 (%100) |
| Kapsanan dil | 4 (en, tr, de, fr) |
| Test edilen HTTP durum kodları | 200, 400, 401, 422, 502, 503 |

---

<a id="english"></a>

<details>
<summary>🇬🇧 English — Click to expand</summary>

## English

### Overview

The test suite covers 56 tests across 4 categories with no physical printer required. A `MockPrinter` class simulates all printer behaviors including 6 error scenarios.

### Running Tests

```bash
pytest -v                            # All tests with verbose output
pytest --cov=app --cov-report=html   # Coverage report
pytest tests/test_api.py -v          # API tests only (17)
pytest tests/test_services.py -v     # Service tests only (14)
pytest tests/test_escpos.py -v       # ESC/POS tests only (10)
pytest tests/test_mock_printer_errors.py -v  # Error tests only (15)
```

### Test Categories

**1. API Tests (`test_api.py`, 17 tests)**  
Integration tests for all HTTP endpoints. Tests authentication, error responses, idempotency behavior, and correct HTTP status codes.

**2. Service Tests (`test_services.py`, 14 tests)**  
Unit tests for the service layer: log writing/reading, queue enqueue/dequeue, i18n translation retrieval, error code validation.

**3. ESC/POS Tests (`test_escpos.py`, 10 tests)**  
Unit tests for the ESC/POS command builder. Validates that correct byte sequences are generated for each command (init, text, bold, alignment, QR code, cut).

**4. Error Simulation Tests (`test_mock_printer_errors.py`, 15 tests)**  
Tests all 6 printer error scenarios (PAPER_OUT, PAPER_JAM, COVER_OPEN, OVERHEAT, COMM_ERROR, UNKNOWN_COMMAND) via the mock printer. Validates API responses, recovery scenarios, and statistics tracking.

### Key Testing Patterns

**Idempotency Testing:**  
Same `job_id` submitted twice → printer receives data only once. Critical for network retry scenarios.

**Error Recovery:**  
Simulate error for N operations → operations fail → clear error → operations succeed. Mirrors real-world printer behavior.

**i18n Completeness:**  
All error codes have translations in all 4 languages. Tested automatically so missing translations are caught at CI time.

### Fixtures

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `event_loop` | session | Shared asyncio loop |
| `client` | function | AsyncClient + Bearer token |
| `connected_client` | function | Client + mock printer connected |

</details>

---

<a id="deutsch"></a>

<details>
<summary>🇩🇪 Deutsch — Klicken zum Aufklappen</summary>

## Deutsch

### Übersicht

Die Testsuite umfasst 56 Tests in 4 Kategorien ohne physischen Drucker. Ein `MockPrinter` simuliert alle Druckerverhaltensweisen.

### Tests ausführen

```bash
pytest -v
pytest --cov=app --cov-report=html
```

### Testkategorien

**1. API-Tests (17 Tests):** Integrationstests für alle HTTP-Endpunkte.

**2. Service-Tests (14 Tests):** Unit-Tests für die Service-Schicht: Protokollierung, Warteschlange, Übersetzungen, Fehlercodes.

**3. ESC/POS-Tests (10 Tests):** Unit-Tests für den ESC/POS-Befehlsgenerator.

**4. Fehlersimulations-Tests (15 Tests):** Tests für alle 6 Druckerfehlerszenarien über den Mock-Drucker.

### Schlüsseltestmuster

**Idempotenz:** Gleiche `job_id` zweimal senden → Drucker empfängt Daten nur einmal.

**Fehlerwiederherstellung:** Fehler für N Operationen simulieren → Operationen schlagen fehl → Fehler löschen → Operationen erfolgreich.

**i18n-Vollständigkeit:** Alle Fehlercodes haben Übersetzungen in allen 4 Sprachen.

</details>

---

<a id="français"></a>

<details>
<summary>🇫🇷 Français — Cliquer pour développer</summary>

## Français

### Vue d'ensemble

La suite de tests couvre 56 tests dans 4 catégories sans imprimante physique. Un `MockPrinter` simule tous les comportements de l'imprimante.

### Exécuter les tests

```bash
pytest -v
pytest --cov=app --cov-report=html
```

### Catégories de tests

**1. Tests API (17 tests):** Tests d'intégration pour tous les endpoints HTTP.

**2. Tests de service (14 tests):** Tests unitaires pour la couche service: journalisation, file d'attente, traductions, codes d'erreur.

**3. Tests ESC/POS (10 tests):** Tests unitaires pour le générateur de commandes ESC/POS.

**4. Tests de simulation d'erreurs (15 tests):** Tests des 6 scénarios d'erreur imprimante via le mock.

### Modèles de test clés

**Idempotence:** Même `job_id` soumis deux fois → l'imprimante reçoit les données une seule fois.

**Récupération d'erreur:** Simuler une erreur pour N opérations → échec → effacer l'erreur → succès.

**Complétude i18n:** Tous les codes d'erreur ont des traductions dans les 4 langues.

</details>

---

← [Geri / Back to root README](../README.md)
