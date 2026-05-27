#!/bin/bash
# Test Script 3: API Entegrasyon Testi

echo "═══════════════════════════════════════════════════════════"
echo "Test 3: API Entegrasyon Testi"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Bu test sahte yazıcının API servisi ile entegrasyonunu test eder."
echo ""
echo "Gereksinimler:"
echo "  - API servisi çalışıyor olmalı (port 8000)"
echo "  - .env dosyası LAN_HOST=127.0.0.1, LAN_PORT=9100 olmalı"
echo ""
read -p "Devam etmek için ENTER'a basın..."

# API servisinin çalıştığını kontrol et
echo ""
echo "→ API servisi kontrol ediliyor..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✗ HATA: API servisi çalışmıyor!"
    echo ""
    echo "API servisini başlatmak için:"
    echo "  cd .."
    echo "  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
    exit 1
fi
echo "✓ API servisi çalışıyor"

# Sahte yazıcıyı arka planda başlat
echo ""
echo "→ Sahte yazıcı başlatılıyor (parse mode)..."
python3 fake_printer.py --mode parse --no-color > /tmp/fake_printer_test3.log 2>&1 &
PRINTER_PID=$!

# Yazıcının başlamasını bekle
sleep 2

# Yazıcının çalıştığını kontrol et
if ! ps -p $PRINTER_PID > /dev/null; then
    echo "✗ HATA: Sahte yazıcı başlatılamadı!"
    cat /tmp/fake_printer_test3.log
    exit 1
fi

echo "✓ Sahte yazıcı başlatıldı (PID: $PRINTER_PID)"

# API'ye bağlan
echo ""
echo "→ API'ye bağlanılıyor..."
CONNECT_RESPONSE=$(curl -s -X POST http://localhost:8000/connect \
  -H "Authorization: Bearer change-me-secret-token" \
  -H "Content-Type: application/json" \
  -d '{"connection_type": "lan", "lan_host": "127.0.0.1", "lan_port": 9100}')

if echo "$CONNECT_RESPONSE" | grep -q "connected"; then
    echo "✓ Yazıcıya bağlanıldı"
else
    echo "✗ Yazıcıya bağlanılamadı!"
    echo "Yanıt: $CONNECT_RESPONSE"
    kill $PRINTER_PID 2>/dev/null
    exit 1
fi

# Metin yazdırma testi
echo ""
echo "→ Metin yazdırma testi..."
PRINT_RESPONSE=$(curl -s -X POST http://localhost:8000/print/text \
  -H "Authorization: Bearer change-me-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "test-001",
    "lines": [
      {"text": "TEST FİŞİ", "bold": true, "align": "center", "font_size": "double"},
      {"text": "Tarih: 2026-05-27", "align": "center"},
      {"text": "Tutar: 100.00 TL", "bold": true, "align": "right"}
    ],
    "cut": true
  }')

if echo "$PRINT_RESPONSE" | grep -q "done"; then
    echo "✓ Metin yazdırma başarılı"
else
    echo "✗ Metin yazdırma başarısız!"
    echo "Yanıt: $PRINT_RESPONSE"
fi

# Kısa bir süre bekle
sleep 1

# Log'u kontrol et
echo ""
echo "→ Sahte yazıcı log'u kontrol ediliyor..."
echo ""
echo "Log çıktısı:"
echo "─────────────────────────────────────────────────────────"
tail -n 20 /tmp/fake_printer_test3.log | grep -E "\[CMD\]|\[TEXT\]|\[CUT\]"
echo "─────────────────────────────────────────────────────────"

# Beklenen komutları kontrol et
EXPECTED_COMMANDS=("ESC @" "ESC a 1" "GS !" "TEST FİŞİ" "GS V")
ALL_FOUND=true

echo ""
echo "→ Beklenen komutlar kontrol ediliyor..."
for cmd in "${EXPECTED_COMMANDS[@]}"; do
    if grep -q "$cmd" /tmp/fake_printer_test3.log; then
        echo "  ✓ '$cmd' bulundu"
    else
        echo "  ✗ '$cmd' bulunamadı!"
        ALL_FOUND=false
    fi
done

# Temizlik
echo ""
echo "→ Temizlik yapılıyor..."
kill $PRINTER_PID 2>/dev/null
wait $PRINTER_PID 2>/dev/null

echo ""
echo "═══════════════════════════════════════════════════════════"
if [ "$ALL_FOUND" = true ]; then
    echo "Test Sonucu: BAŞARILI"
    echo "═══════════════════════════════════════════════════════════"
    exit 0
else
    echo "Test Sonucu: BAŞARISIZ"
    echo "═══════════════════════════════════════════════════════════"
    exit 1
fi
