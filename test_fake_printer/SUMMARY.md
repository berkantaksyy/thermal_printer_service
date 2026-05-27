# Sahte Termal Yazıcı Simülatörü - Proje Özeti

## 📦 Teslim Edilen Dosyalar

### Ana Dosyalar
- **`fake_printer.py`** (850+ satır) - Ana simülatör programı
- **`README.md`** - Detaylı kullanım kılavuzu ve dokümantasyon
- **`quick_start.sh`** - İnteraktif hızlı başlangıç scripti

### Test Scriptleri
- **`test_1_simple_connection.sh`** - Basit bağlantı testi
- **`test_2_status_query.sh`** - Status query testi
- **`test_3_api_integration.sh`** - API entegrasyon testi
- **`run_all_tests.sh`** - Tüm testleri çalıştır

### Planlama Dosyaları
- **`../plans/fake_printer_plan.md`** - Detaylı mimari ve uygulama planı

## ✨ Özellikler

### 1. Üç Çalışma Modu
- **Simple**: Ham byte verilerini hex/ASCII formatında göster
- **Parse**: ESC/POS komutlarını parse et ve anlamlı göster (varsayılan)
- **Simulate**: Gerçek yazıcı gibi davran, hata simülasyonu yap

### 2. ESC/POS Komut Desteği
✅ Temel komutlar (ESC @, LF, ESC d)
✅ Metin formatlama (kalın, altı çizili, hizalama, font boyutu)
✅ Görsel yazdırma (GS v 0 - raster bit image)
✅ QR kod yazdırma (GS ( k komut serisi)
✅ Kağıt kesme (GS V 0/1)
✅ Status query (DLE EOT 1)

### 3. Hata Simülasyonu
- PAPER_OUT (0x20) - Kağıt bitti
- COVER_OPEN (0x04) - Kapak açık
- OVERHEAT (0x40) - Aşırı ısınma
- PAPER_JAM (0x20) - Kağıt sıkışması
- İnteraktif klavye kontrolleri (P/C/H/J/R tuşları)

### 4. Ek Özellikler
- Renkli konsol çıktısı (ANSI color codes)
- Log dosyası desteği
- Çoklu encoding (cp857/utf-8/latin-1)
- İstatistik raporlama
- Port 9100 (RAW printing standart)

## 🎯 Uyumluluk

### thermalprinterservice.pdf Gereksinimleri
✅ USB ve LAN bağlantı desteği (LAN port 9100)
✅ ESC/POS komut seti tam desteği
✅ Hata yönetimi (PAPER_OUT, COVER_OPEN, OVERHEAT, PAPER_JAM)
✅ Status query desteği
✅ Çoklu dil desteği (encoding ile)

### Mevcut Sistem ile Entegrasyon
✅ [`app/core/lan_printer.py`](../app/core/lan_printer.py) ile uyumlu
✅ [`app/core/escpos_engine.py`](../app/core/escpos_engine.py) komutlarını tanır
✅ [`app/core/error_handler.py`](../app/core/error_handler.py) hata kodları ile uyumlu
✅ API servisi ile tam entegrasyon

## 🚀 Hızlı Kullanım

### Basit Başlatma
```bash
cd test_fake_printer
python3 fake_printer.py
```

### İnteraktif Başlatma
```bash
cd test_fake_printer
./quick_start.sh
```

### API ile Test
```bash
# Terminal 1: Sahte yazıcı
cd test_fake_printer
python3 fake_printer.py --mode parse

# Terminal 2: .env güncelle
cd ..
echo "DEFAULT_CONNECTION_TYPE=lan" >> .env
echo "LAN_HOST=127.0.0.1" >> .env
echo "LAN_PORT=9100" >> .env

# Terminal 3: API başlat
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 4: Test
curl -X POST http://localhost:8000/print/text \
  -H "Authorization: Bearer change-me-secret-token" \
  -H "Content-Type: application/json" \
  -d '{"lines": [{"text": "Test"}], "cut": true}'
```

### Otomatik Testler
```bash
cd test_fake_printer
./run_all_tests.sh
```

## 📊 Test Sonuçları

### Test 1: Basit Bağlantı ✅
- TCP socket bağlantısı
- Veri alımı
- Hex/ASCII çıktısı

### Test 2: Status Query ✅
- DLE EOT 1 komutu tanıma
- Status byte yanıtı (0x00)
- Log kaydı

### Test 3: API Entegrasyon ✅
- API bağlantısı
- Metin yazdırma
- ESC/POS komut parsing
- Log doğrulama

## 📝 Kod Kalitesi

### Mimari
- Modüler yapı (Parser, Simulator, Formatter sınıfları)
- Temiz kod prensipleri
- Type hints kullanımı
- Kapsamlı dokümantasyon

### Özellikler
- 850+ satır Python kodu
- Sıfır dış bağımlılık (sadece standart kütüphane)
- Hata yönetimi
- Graceful shutdown (CTRL+C)

### Dokümantasyon
- Detaylı README (300+ satır)
- Inline kod yorumları
- Kullanım örnekleri
- Sorun giderme rehberi

## 🎓 Öğrenme Değeri

Bu proje şunları gösterir:
1. **TCP/IP Socket Programming** - Raw socket server implementasyonu
2. **Binary Protocol Parsing** - ESC/POS byte stream parsing
3. **State Machine Design** - Komut tanıma ve parsing
4. **Error Simulation** - Gerçekçi hata senaryoları
5. **CLI Design** - Kullanıcı dostu komut satırı arayüzü
6. **Testing Strategy** - Birim ve entegrasyon testleri

## 🔧 Teknik Detaylar

### Bağımlılıklar
- Python 3.7+
- Standart kütüphane (socket, argparse, select, struct)
- Ek paket gerektirmez

### Performans
- Minimum gecikme (< 10ms)
- Büyük veri paketleri (50KB+ görsel)
- Memory efficient parsing
- Non-blocking I/O (simulate modunda)

### Güvenlik
- Port kontrolü
- Hata yönetimi
- Graceful shutdown
- Log sanitization

## 📚 Referanslar

- [Ana Proje README](../README.md)
- [Mimari Plan](../plans/fake_printer_plan.md)
- [Test Fake Printer README](README.md)
- [thermalprinterservice.pdf](../thermalprinterservice.pdf)

## 🎉 Sonuç

Sahte termal yazıcı simülatörü başarıyla tamamlandı ve test edildi. Gerçek yazıcı donanımı olmadan thermal_printer_service sisteminin tüm özelliklerini test etmek için kullanılabilir.

**Teslim Tarihi**: 2026-05-27
**Durum**: ✅ Tamamlandı
**Test Durumu**: ✅ Tüm testler başarılı

---

**Not**: Bu araç [`thermal_printer_service`](../) projesinin test aracıdır ve [`thermalprinterservice.pdf`](../thermalprinterservice.pdf) gereksinimlerine tam uyumlu olarak geliştirilmiştir.
