# Sahte Termal Yazıcı Simülatörü

Cashino KP-300/KP-301H termal yazıcılarını simüle eden TCP/IP server. Gerçek yazıcı donanımı olmadan [`thermal_printer_service`](../README.md) sistemini test etmek için kullanılır.

## 🚀 Hızlı Başlangıç

```bash
# Basit kullanım (parse modu)
python3 fake_printer.py

# Belirli bir modda çalıştır
python3 fake_printer.py --mode simulate

# Yardım
python3 fake_printer.py --help
```

## 📋 Özellikler

- ✅ **3 Çalışma Modu**: Simple, Parse, Simulate
- ✅ **ESC/POS Komut Desteği**: Metin, görsel, QR kod, kesme, formatlama
- ✅ **Status Query**: DLE EOT komutlarına yanıt verme
- ✅ **Hata Simülasyonu**: PAPER_OUT, COVER_OPEN, OVERHEAT, PAPER_JAM
- ✅ **Port 9100**: RAW printing standart portu
- ✅ **Çoklu Encoding**: cp857 (Türkçe), utf-8, latin-1
- ✅ **Renkli Çıktı**: ANSI renk kodları ile okunabilir loglar
- ✅ **Log Dosyası**: Tüm işlemleri dosyaya kaydetme

## 🎮 Çalışma Modları

### 1. Simple Mode (Basit)

Ham byte verilerini hex ve ASCII formatında gösterir. Hızlı bağlantı testi için idealdir.

```bash
python3 fake_printer.py --mode simple
```

**Çıktı Örneği:**
```
[RECV 15 bytes] 1B 40 1B 61 01 48 65 6C 6C 6F 0A 1D 56 00
[ASCII] .@.a.Hello...V.
```

### 2. Parse Mode (Gelişmiş) - Varsayılan

ESC/POS komutlarını parse eder ve anlamlı şekilde gösterir.

```bash
python3 fake_printer.py --mode parse
```

**Çıktı Örneği:**
```
[+] Bağlantı: 192.168.1.50:54321
[CMD] ESC @ - Yazıcı başlatıldı
[CMD] ESC a 1 - Hizalama: CENTER
[CMD] GS ! 0x11 - Font: Double (2x2)
[TEXT] "ACO RECYCLING"
[CMD] LF - Satır atla
[CUT] GS V 0 - Kağıt kes (Full)
```

### 3. Simulate Mode (Tam Simülasyon)

Gerçek yazıcı gibi davranır, status query'lere yanıt verir, interaktif hata simülasyonu yapar.

```bash
python3 fake_printer.py --mode simulate
```

**Çıktı Örneği:**
```
[+] Bağlantı: 192.168.1.50:54321
[STATUS] Kağıt: ✓ OK | Kapak: ✓ OK | Sıcaklık: ✓ OK
[CMD] ESC @ - Yazıcı başlatıldı
[TEXT] "ACO RECYCLING"
[PRINT] ✓ 45 byte yazdırıldı
[CUT] ✓ Kağıt kesildi

Hata simülasyonu için tuşlar:
  [P] Paper Out  [C] Cover Open  [H] Overheat  [R] Reset
```

## 🔧 Komut Satırı Seçenekleri

```bash
python3 fake_printer.py [OPTIONS]

Seçenekler:
  --mode {simple,parse,simulate}  Çalışma modu (varsayılan: parse)
  --host HOST                     Dinlenecek IP (varsayılan: 0.0.0.0)
  --port PORT                     Dinlenecek port (varsayılan: 9100)
  --encoding {cp857,utf-8,latin-1} Metin encoding (varsayılan: cp857)
  --log FILE                      Log dosyası (opsiyonel)
  --no-color                      Renkli çıktıyı devre dışı bırak
  --help                          Yardım mesajı
```

## 🧪 Test Senaryoları

### Test 1: Basit Bağlantı Testi

```bash
# Terminal 1
python3 fake_printer.py --mode simple

# Terminal 2
echo "Test" | nc localhost 9100
```

**Beklenen Çıktı (Terminal 1):**
```
[+] Bağlantı: 127.0.0.1:xxxxx
[RECV 5 bytes] 54 65 73 74 0A
[ASCII] Test.
```

### Test 2: API ile Metin Yazdırma

```bash
# Terminal 1: Sahte yazıcıyı başlat
python3 fake_printer.py --mode parse

# Terminal 2: .env dosyasını güncelle
cd ..
cat > .env << EOF
DEFAULT_CONNECTION_TYPE=lan
LAN_HOST=127.0.0.1
LAN_PORT=9100
API_BEARER_TOKEN=change-me-secret-token
EOF

# Terminal 3: API servisini başlat
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 4: Test isteği gönder
curl -X POST http://localhost:8000/print/text \
  -H "Authorization: Bearer change-me-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "lines": [
      {"text": "TEST FİŞİ", "bold": true, "align": "center", "font_size": "double"},
      {"text": "Tarih: 2026-05-27", "align": "center"},
      {"text": "Tutar: 100.00 TL", "bold": true, "align": "right"}
    ],
    "cut": true
  }'
```

**Beklenen Çıktı (Terminal 1):**
```
[+] Bağlantı: 127.0.0.1:xxxxx
[CMD] ESC @ - Yazıcı başlatıldı
[CMD] ESC a 1 - Hizalama: CENTER
[CMD] GS ! 0x11 - Font: Double (2x2)
[CMD] ESC E 1 - Kalın: ON
[TEXT] "TEST FİŞİ"
[CMD] LF - Satır atla
[CMD] ESC E 0 - Kalın: OFF
[CMD] GS ! 0x00 - Font: Normal (1x1)
[CMD] ESC a 1 - Hizalama: CENTER
[TEXT] "Tarih: 2026-05-27"
[CMD] LF - Satır atla
[CMD] ESC a 2 - Hizalama: RIGHT
[CMD] ESC E 1 - Kalın: ON
[TEXT] "Tutar: 100.00 TL"
[CMD] LF - Satır atla
[CMD] ESC d 3 - 3 satır besle
[CUT] GS V 0 - Kağıt kes (Full)
```

### Test 3: QR Kod Yazdırma

```bash
# Terminal 1
python3 fake_printer.py --mode parse

# Terminal 2
curl -X POST http://localhost:8000/print/qr \
  -H "Authorization: Bearer change-me-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "data": "https://example.com/receipt/12345",
    "size": 6,
    "error_correction": "M",
    "label": "Detaylar için tarayın",
    "cut": true
  }'
```

**Beklenen Çıktı:**
```
[+] Bağlantı: 127.0.0.1:xxxxx
[CMD] ESC @ - Yazıcı başlatıldı
[CMD] ESC a 1 - Hizalama: CENTER
[QR] Model ayarlandı: Model 2
[QR] Boyut: 6
[QR] Hata düzeltme: M
[QR] Data: "https://example.com/receipt/12345" (35 bytes)
[QR] Yazdır komutu
[CMD] LF - Satır atla
[TEXT] "Detaylar için tarayın"
[CMD] LF - Satır atla
[CUT] GS V 0 - Kağıt kes (Full)
```

### Test 4: Hata Simülasyonu

```bash
# Terminal 1: Simulate modunda başlat
python3 fake_printer.py --mode simulate

# Konsolda 'P' tuşuna bas (Paper Out simüle et)

# Terminal 2: Yazdırma isteği gönder
curl -X POST http://localhost:8000/print/text \
  -H "Authorization: Bearer change-me-secret-token" \
  -H "Content-Type: application/json" \
  -d '{"lines": [{"text": "Test"}], "cut": true}'
```

**Beklenen Çıktı (Terminal 1):**
```
[!] HATA SİMÜLE EDİLDİ: PAPER_OUT
[STATUS] Kağıt: ✗ OUT | Kapak: ✓ OK | Sıcaklık: ✓ OK

[+] Bağlantı: 127.0.0.1:xxxxx
[STATUS QUERY] DLE EOT 1
[RESPONSE] 0x20 (Error 0x20)
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

### Test 5: Status Query

```bash
# Terminal 1
python3 fake_printer.py --mode simulate

# Terminal 2 (Python)
python3 << 'EOF'
import socket

s = socket.socket()
s.connect(('localhost', 9100))

# Status query gönder
s.send(b'\x10\x04\x01')  # DLE EOT 1

# Yanıtı al
status = s.recv(1)
print(f"Status byte: 0x{status[0]:02X}")

# Durumu decode et
if status[0] == 0x00:
    print("✓ Yazıcı normal durumda")
elif status[0] & 0x20:
    print("✗ Kağıt bitti (PAPER_OUT)")
elif status[0] & 0x04:
    print("✗ Kapak açık (COVER_OPEN)")
elif status[0] & 0x40:
    print("✗ Aşırı ısınma (OVERHEAT)")

s.close()
EOF
```

### Test 6: Görsel Yazdırma

```bash
# Terminal 1
python3 fake_printer.py --mode parse

# Terminal 2: Basit bir test görseli oluştur ve yazdır
python3 << 'EOF'
import base64
import requests
from PIL import Image
import io

# 100x100 siyah-beyaz test görseli oluştur
img = Image.new('1', (100, 100), 1)
for i in range(0, 100, 10):
    for j in range(100):
        img.putpixel((i, j), 0)

# Base64'e çevir
buffer = io.BytesIO()
img.save(buffer, format='PNG')
img_base64 = base64.b64encode(buffer.getvalue()).decode()

# API'ye gönder
response = requests.post(
    'http://localhost:8000/print/image',
    headers={'Authorization': 'Bearer change-me-secret-token'},
    json={
        'image_base64': img_base64,
        'align': 'center',
        'cut': True
    }
)

print(f"Status: {response.status_code}")
print(response.json())
EOF
```

## 🎯 Hata Simülasyonu (Simulate Modunda)

Simulate modunda çalışırken, klavyeden aşağıdaki tuşlara basarak hata simüle edebilirsiniz:

| Tuş | Hata | Status Byte | Açıklama |
|-----|------|-------------|----------|
| **P** | PAPER_OUT | 0x20 | Kağıt bitti |
| **C** | COVER_OPEN | 0x04 | Kapak açık |
| **H** | OVERHEAT | 0x40 | Aşırı ısınma |
| **J** | PAPER_JAM | 0x20 | Kağıt sıkışması |
| **R** | RESET | 0x00 | Tüm hataları temizle |

## 📊 İstatistikler

Program kapatıldığında (CTRL+C) aşağıdaki istatistikler gösterilir:

```
📊 İstatistikler:
  Toplam bağlantı: 5
  Toplam byte alındı: 2,450
  Toplam komut: 47
  Yazdırma işlemi: 5
  Kesme işlemi: 5
```

## 📝 Log Dosyası

Tüm işlemleri dosyaya kaydetmek için:

```bash
python3 fake_printer.py --mode parse --log printer.log
```

Log dosyası ANSI renk kodları olmadan, timestamp'li olarak kaydedilir:

```
[2026-05-27 12:00:00] [+] Bağlantı: 127.0.0.1:54321
[2026-05-27 12:00:01] [CMD] ESC @ - Yazıcı başlatıldı
[2026-05-27 12:00:01] [TEXT] "Test"
[2026-05-27 12:00:01] [CUT] GS V 0 - Kağıt kes (Full)
```

## 🔍 Desteklenen ESC/POS Komutları

### Temel Komutlar
- `ESC @` (0x1B 0x40) - Yazıcı başlatma
- `LF` (0x0A) - Satır atlama
- `ESC d n` - n satır besleme

### Metin Formatlama
- `ESC E 0/1` - Kalın yazı
- `ESC - 0/1` - Altı çizili
- `ESC a 0/1/2` - Hizalama (sol/orta/sağ)
- `GS ! n` - Font boyutu

### Görsel ve QR
- `GS v 0` - Raster bit image
- `GS ( k` - QR kod komutları

### Kesme
- `GS V 0` - Tam kesme
- `GS V 1` - Kısmi kesme

### Status Query
- `DLE EOT 1` (0x10 0x04 0x01) - Durum sorgulama

## 🐛 Sorun Giderme

### Port zaten kullanımda

```
✗ Hata: Port 9100 zaten kullanımda!
Başka bir port deneyin: --port 9101
```

**Çözüm:**
```bash
# Başka bir port kullan
python3 fake_printer.py --port 9101

# veya kullanımdaki portu bul ve kapat
lsof -i :9100
kill -9 <PID>
```

### Bağlantı gelmiyor

1. Firewall kontrolü:
```bash
# macOS
sudo pfctl -d  # Firewall'u geçici olarak kapat

# Linux
sudo ufw allow 9100
```

2. API servisinin doğru yapılandırıldığından emin olun:
```bash
# .env dosyasını kontrol et
cat ../.env | grep LAN
```

Şu değerleri görmelisiniz:
```
LAN_HOST=127.0.0.1
LAN_PORT=9100
```

### Türkçe karakterler bozuk

```bash
# UTF-8 encoding kullan
python3 fake_printer.py --encoding utf-8

# veya latin-1
python3 fake_printer.py --encoding latin-1
```

## 📚 Ek Kaynaklar

- [Ana Proje README](../README.md)
- [Mimari Plan](../plans/fake_printer_plan.md)
- [ESC/POS Engine](../app/core/escpos_engine.py)
- [LAN Printer](../app/core/lan_printer.py)

## 🤝 Katkıda Bulunma

Bu araç [`thermal_printer_service`](../) projesinin test aracıdır. Geliştirmeler için ana projeye katkıda bulunabilirsiniz.

## 📄 Lisans

MIT License - Ana proje ile aynı lisans altındadır.
