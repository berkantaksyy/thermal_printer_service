# fake_printer.py - Detaylı Mimari ve Uygulama Planı

## 📋 Genel Bakış

[`thermalprinterservice.pdf`](../thermalprinterservice.pdf) dokümanına ve mevcut [`app/core/lan_printer.py`](../app/core/lan_printer.py) sistemine tam uyumlu bir sahte termal yazıcı simülatörü. Bu araç, gerçek yazıcı donanımı olmadan sistemi test etmek için kullanılacak.

## 🎯 Temel Gereksinimler

### 1. Bağlantı Yönetimi
- **Port**: 9100 (RAW printing standart portu)
- **Host**: 0.0.0.0 (tüm IP'lerden bağlantı kabul et)
- **Protokol**: TCP/IP socket server
- **Çoklu Bağlantı**: Sıralı bağlantıları destekle (aynı anda tek client)

### 2. ESC/POS Komut Desteği
[`app/core/escpos_engine.py`](../app/core/escpos_engine.py) tarafından üretilen tüm komutları tanımalı:

#### Temel Komutlar
- `ESC @` (0x1B 0x40) - Yazıcı başlatma/reset
- `0x0A` - Line feed (satır atlama)
- `GS V 0/1` (0x1D 0x56 0x00/0x01) - Kağıt kesme (full/partial)

#### Metin Formatlama
- `ESC E 0/1` - Kalın yazı açma/kapama
- `ESC - 0/1` - Altı çizili açma/kapama
- `ESC a 0/1/2` - Hizalama (sol/orta/sağ)
- `GS ! n` - Font boyutu (normal/2x yükseklik/2x genişlik/2x2)

#### Görsel Yazdırma
- `GS v 0` - Raster bit image komutu
- Format: `GS v 0 m xL xH yL yH [data...]`

#### QR Kod Yazdırma
- `GS ( k` - QR kod komut serisi
- Model seçimi, boyut, hata düzeltme, veri saklama, yazdırma

#### Status Query
- `DLE EOT 1` (0x10 0x04 0x01) - Durum sorgulama
- **Yanıt**: 1 byte status byte
  - Bit 5 (0x20): PAPER_OUT
  - Bit 2 (0x04): COVER_OPEN
  - Bit 6 (0x40): OVERHEAT

### 3. Çalışma Modları

#### Mod 1: Simple (Basit)
```bash
python3 fake_printer.py --mode simple
```
- Gelen tüm byte'ları hex ve ASCII formatında göster
- Minimum parsing, maksimum hız
- Hızlı bağlantı testi için ideal

**Çıktı Örneği:**
```
[+] Bağlantı: 192.168.1.50:54321
[RECV 15 bytes] 1B 40 1B 61 01 48 65 6C 6C 6F 0A 1D 56 00
[ASCII] .@.a.Hello...V.
```

#### Mod 2: Parse (Gelişmiş)
```bash
python3 fake_printer.py --mode parse
```
- ESC/POS komutlarını parse et ve anlamlı göster
- Metin içeriğini decode et (cp857/utf-8)
- Görsel ve QR boyutlarını göster
- Varsayılan mod

**Çıktı Örneği:**
```
[+] Bağlantı: 192.168.1.50:54321
[CMD] ESC @ - Yazıcı başlatıldı
[CMD] ESC a 1 - Hizalama: CENTER
[CMD] GS ! 17 - Font: 2x2 (double)
[TEXT] "ACO RECYCLING"
[CMD] LF - Satır atla
[CMD] ESC a 1 - Hizalama: CENTER
[TEXT] "Ödül: 3.00 TL"
[CMD] LF - Satır atla
[CMD] GS V 0 - Kağıt kes (full cut)
```

#### Mod 3: Simulate (Tam Simülasyon)
```bash
python3 fake_printer.py --mode simulate
```
- Gerçek yazıcı gibi davran
- Status query'lere yanıt ver
- Hata simülasyonu yap (interaktif)
- En gerçekçi test ortamı

**Çıktı Örneği:**
```
[+] Bağlantı: 192.168.1.50:54321
[STATUS] Kağıt: OK | Kapak: OK | Sıcaklık: OK
[CMD] ESC @ - Yazıcı başlatıldı
[TEXT] "ACO RECYCLING"
[PRINT] ✓ 45 byte yazdırıldı
[CUT] ✓ Kağıt kesildi

Hata simülasyonu için tuşlar:
  [P] Paper Out  [C] Cover Open  [H] Overheat  [R] Reset
```

### 4. Hata Simülasyon Sistemi

[`app/core/error_handler.py`](../app/core/error_handler.py) ile uyumlu hata kodları:

| Hata Kodu | Status Byte | Simülasyon Tuşu | Açıklama |
|-----------|-------------|-----------------|----------|
| `PAPER_OUT` | 0x20 | P | Kağıt bitti |
| `COVER_OPEN` | 0x04 | C | Kapak açık |
| `OVERHEAT` | 0x40 | H | Aşırı ısınma |
| `PAPER_JAM` | 0x20 | J | Kağıt sıkışması |
| Normal | 0x00 | R | Tüm hataları temizle |

**Simülasyon Davranışı:**
- Hata aktifken status query doğru byte'ı döndür
- Hata aktifken print komutları başarısız olabilir (opsiyonel)
- Konsolda hata durumunu göster

### 5. Komut Satırı Arayüzü

```bash
python3 fake_printer.py [OPTIONS]

Seçenekler:
  --mode {simple,parse,simulate}  Çalışma modu (varsayılan: parse)
  --host HOST                     Dinlenecek IP (varsayılan: 0.0.0.0)
  --port PORT                     Dinlenecek port (varsayılan: 9100)
  --log FILE                      Log dosyası (opsiyonel)
  --encoding {cp857,utf-8,latin-1} Metin encoding (varsayılan: cp857)
  --help                          Yardım mesajı
```

**Kullanım Örnekleri:**
```bash
# Basit mod, hızlı test
python3 fake_printer.py --mode simple

# Parse modu, varsayılan ayarlar
python3 fake_printer.py

# Tam simülasyon, özel port
python3 fake_printer.py --mode simulate --port 9101

# Log dosyasına kaydet
python3 fake_printer.py --mode parse --log printer.log
```

## 🏗️ Mimari Tasarım

### Modüler Yapı

```
fake_printer.py
├── FakePrinterServer (Ana sınıf)
│   ├── __init__(host, port, mode, encoding)
│   ├── start() - Server başlat
│   ├── handle_client(conn, addr) - Client bağlantısı yönet
│   └── stop() - Server durdur
│
├── ESCPOSParser (Komut parser)
│   ├── parse_stream(data) - Byte stream'i parse et
│   ├── identify_command(bytes) - Komutu tanımla
│   ├── extract_text(bytes, encoding) - Metin çıkar
│   └── format_output(cmd, data) - Formatlanmış çıktı
│
├── StatusSimulator (Durum simülatörü)
│   ├── __init__()
│   ├── get_status_byte() - Mevcut status byte'ı döndür
│   ├── set_error(error_code) - Hata simüle et
│   ├── clear_errors() - Hataları temizle
│   └── handle_keyboard() - Klavye girişi (simulate modunda)
│
└── OutputFormatter (Çıktı formatı)
    ├── simple_format(data) - Basit hex/ASCII
    ├── parse_format(cmd, data) - Parse edilmiş komut
    └── simulate_format(cmd, data, status) - Simülasyon çıktısı
```

### Veri Akışı

```mermaid
graph TD
    A[LAN Printer Client] -->|TCP 9100| B[FakePrinterServer]
    B -->|Raw Bytes| C{Mode?}
    
    C -->|simple| D[Simple Output]
    C -->|parse| E[ESCPOSParser]
    C -->|simulate| F[StatusSimulator]
    
    E -->|Parsed Commands| G[Parse Output]
    F -->|Status + Commands| H[Simulate Output]
    
    D --> I[Console]
    G --> I
    H --> I
    
    F -->|Status Query| J[Send Status Byte]
    J -->|0x10 0x04 0x01| A
    
    K[Keyboard Input] -->|P/C/H/R| F
```

## 📝 Detaylı Uygulama Adımları

### Adım 1: Temel Socket Server
- TCP socket server oluştur (0.0.0.0:9100)
- Client bağlantılarını kabul et
- Veri alımını yönet
- Graceful shutdown (CTRL+C)

### Adım 2: Simple Mode
- Raw byte'ları hex formatında göster
- ASCII karşılıklarını göster (printable chars)
- Bağlantı bilgilerini logla
- Minimum overhead

### Adım 3: ESC/POS Parser
- Komut tanımlama tablosu oluştur
- State machine ile byte stream parse et
- Metin encoding desteği (cp857, utf-8, latin-1)
- Görsel ve QR metadata çıkarma

### Adım 4: Status Simulator
- Status byte yönetimi
- DLE EOT komutunu tanı ve yanıtla
- Hata durumu simülasyonu
- Klavye input handling (non-blocking)

### Adım 5: Simulate Mode
- Gerçekçi yazıcı davranışı
- Status query yanıtları
- İnteraktif hata simülasyonu
- Detaylı operasyon logları

### Adım 6: CLI ve Dokümantasyon
- argparse ile komut satırı arayüzü
- Help mesajları
- Kullanım örnekleri
- README güncellemesi

## 🧪 Test Senaryoları

### Test 1: Basit Bağlantı
```bash
# Terminal 1
python3 fake_printer.py --mode simple

# Terminal 2
echo "Test" | nc localhost 9100
```

**Beklenen Çıktı:**
```
[+] Bağlantı: 127.0.0.1:xxxxx
[RECV 5 bytes] 54 65 73 74 0A
[ASCII] Test.
```

### Test 2: API ile Metin Yazdırma
```bash
# Terminal 1
python3 fake_printer.py --mode parse

# Terminal 2
curl -X POST http://localhost:8000/print/text \
  -H "Authorization: Bearer change-me-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "lines": [
      {"text": "TEST FİŞİ", "bold": true, "align": "center", "font_size": "double"}
    ],
    "cut": true
  }'
```

**Beklenen Çıktı:**
```
[+] Bağlantı: 127.0.0.1:xxxxx
[CMD] ESC @ - Yazıcı başlatıldı
[CMD] ESC a 1 - Hizalama: CENTER
[CMD] GS ! 17 - Font: 2x2
[CMD] ESC E 1 - Kalın: ON
[TEXT] "TEST FİŞİ"
[CMD] LF
[CMD] ESC E 0 - Kalın: OFF
[CMD] ESC d 3 - 3 satır besle
[CMD] GS V 0 - Kağıt kes
```

### Test 3: Status Query
```bash
# Terminal 1
python3 fake_printer.py --mode simulate

# Terminal 2 (Python)
import socket
s = socket.socket()
s.connect(('localhost', 9100))
s.send(b'\x10\x04\x01')  # DLE EOT 1
status = s.recv(1)
print(f"Status: 0x{status[0]:02X}")
```

**Beklenen Çıktı (Terminal 1):**
```
[+] Bağlantı: 127.0.0.1:xxxxx
[STATUS QUERY] DLE EOT 1
[RESPONSE] 0x00 (Normal - Tüm sistemler OK)
```

### Test 4: Hata Simülasyonu
```bash
# Terminal 1
python3 fake_printer.py --mode simulate
# Konsolda 'P' tuşuna bas (Paper Out)

# Terminal 2
curl -X POST http://localhost:8000/print/text \
  -H "Authorization: Bearer change-me-secret-token" \
  -H "Content-Type: application/json" \
  -d '{"lines": [{"text": "Test"}], "cut": true}'
```

**Beklenen Çıktı (Terminal 1):**
```
[!] HATA SİMÜLE EDİLDİ: PAPER_OUT
[STATUS] Kağıt: ✗ OUT | Kapak: OK | Sıcaklık: OK

[+] Bağlantı: 127.0.0.1:xxxxx
[STATUS QUERY] DLE EOT 1
[RESPONSE] 0x20 (PAPER_OUT)
```

**Beklenen Çıktı (Terminal 2):**
```json
{
  "detail": {
    "error": {
      "code": "PAPER_OUT",
      "detail": "Kağıt bitti. Lütfen kağıt yükleyin ve tekrar deneyin."
    },
    "job_id": "..."
  }
}
```

### Test 5: QR Kod Yazdırma
```bash
# Terminal 1
python3 fake_printer.py --mode parse

# Terminal 2
curl -X POST http://localhost:8000/print/qr \
  -H "Authorization: Bearer change-me-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "data": "https://example.com",
    "size": 6,
    "error_correction": "M",
    "label": "Scan me!",
    "cut": true
  }'
```

**Beklenen Çıktı:**
```
[+] Bağlantı: 127.0.0.1:xxxxx
[CMD] ESC @ - Yazıcı başlatıldı
[CMD] ESC a 1 - Hizalama: CENTER
[QR] Model: 2, Size: 6, EC: M
[QR] Data: "https://example.com" (19 bytes)
[QR] Print command
[TEXT] "Scan me!"
[CMD] GS V 0 - Kağıt kes
```

### Test 6: Görsel Yazdırma
```bash
# Terminal 1
python3 fake_printer.py --mode parse

# Terminal 2
curl -X POST http://localhost:8000/print/image \
  -H "Authorization: Bearer change-me-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "iVBORw0KGgo...",
    "align": "center",
    "cut": true
  }'
```

**Beklenen Çıktı:**
```
[+] Bağlantı: 127.0.0.1:xxxxx
[CMD] ESC @ - Yazıcı başlatıldı
[CMD] ESC a 1 - Hizalama: CENTER
[IMAGE] Raster bit image
[IMAGE] Boyut: 576x200 pixels (14400 bytes)
[CMD] LF
[CMD] GS V 0 - Kağıt kes
```

## 📚 Ek Özellikler (Opsiyonel)

### 1. Log Dosyası Desteği
```bash
python3 fake_printer.py --log printer.log
```
- Tüm işlemleri dosyaya kaydet
- Timestamp'li loglar
- Hem konsol hem dosya çıktısı

### 2. Çoklu Encoding Desteği
```bash
python3 fake_printer.py --encoding utf-8
```
- cp857 (Türkçe - varsayılan)
- utf-8 (Unicode)
- latin-1 (Batı Avrupa)

### 3. Renkli Konsol Çıktısı
- Komutlar: Mavi
- Metin: Yeşil
- Hatalar: Kırmızı
- Status: Sarı
- ANSI color codes kullan

### 4. İstatistikler
```
[İSTATİSTİKLER]
Toplam bağlantı: 5
Toplam byte alındı: 2,450
Toplam komut: 47
Yazdırma işlemi: 5
Kesme işlemi: 5
Ortalama işlem süresi: 0.15s
```

## 🔧 Teknik Detaylar

### Bağımlılıklar
```python
# Standart kütüphane - ek kurulum gerektirmez
import socket
import argparse
import sys
import select  # Non-blocking keyboard input için
import struct
from datetime import datetime
from typing import Optional, Tuple, List
```

### Performans
- Minimum gecikme (< 10ms)
- Büyük veri paketlerini destekle (görsel için 50KB+)
- Memory efficient byte parsing
- Non-blocking I/O

### Hata Yönetimi
- Graceful shutdown (CTRL+C)
- Client disconnect handling
- Invalid data handling
- Port already in use kontrolü

## 📖 Dokümantasyon

### README.md Güncellemesi
```markdown
## Test Ortamı Kurulumu

### Sahte Yazıcı ile Test

Gerçek yazıcı donanımı olmadan sistemi test etmek için:

1. Sahte yazıcıyı başlat:
   ```bash
   python3 fake_printer.py --mode parse
   ```

2. .env dosyasını güncelle:
   ```env
   DEFAULT_CONNECTION_TYPE=lan
   LAN_HOST=127.0.0.1
   LAN_PORT=9100
   ```

3. API servisini başlat:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

4. Test et:
   ```bash
   curl -X POST http://localhost:8000/print/text \
     -H "Authorization: Bearer change-me-secret-token" \
     -H "Content-Type: application/json" \
     -d '{"lines": [{"text": "Test"}], "cut": true}'
   ```

Detaylı kullanım için: [`fake_printer.py --help`](fake_printer.py)
```

## ✅ Başarı Kriterleri

1. ✅ Port 9100'de TCP bağlantı kabul ediyor
2. ✅ 3 farklı mod çalışıyor (simple/parse/simulate)
3. ✅ ESC/POS komutlarını doğru parse ediyor
4. ✅ Status query'lere yanıt veriyor
5. ✅ Hata simülasyonu çalışıyor
6. ✅ API ile entegre test başarılı
7. ✅ Türkçe karakter desteği (cp857)
8. ✅ Dokümantasyon eksiksiz
9. ✅ Kullanımı kolay ve anlaşılır

## 🚀 Sonraki Adımlar

1. **Temel implementasyon** - Socket server ve simple mode
2. **Parser geliştirme** - ESC/POS komut tanıma
3. **Simülasyon özellikleri** - Status ve hata yönetimi
4. **Test ve iyileştirme** - Tüm senaryoları test et
5. **Dokümantasyon** - README ve kullanım kılavuzu

---

**Not**: Bu plan [`thermalprinterservice.pdf`](../thermalprinterservice.pdf) gereksinimlerine ve mevcut [`app/core/lan_printer.py`](../app/core/lan_printer.py) + [`app/core/escpos_engine.py`](../app/core/escpos_engine.py) implementasyonuna tam uyumlu olarak hazırlanmıştır.
