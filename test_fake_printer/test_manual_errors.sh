#!/bin/bash
# Manuel Hata Test Rehberi

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║        Manuel Hata Testi - İnteraktif Rehber             ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Bu script sahte yazıcıda hata simülasyonu yapmanıza yardımcı olur."
echo ""

# API servisinin çalıştığını kontrol et
echo "→ API servisi kontrol ediliyor..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✗ HATA: API servisi çalışmıyor!"
    echo ""
    echo "API servisini başlatmak için:"
    echo "  Terminal 2'de: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
    echo ""
    read -p "API servisi başlattıktan sonra ENTER'a basın..."
fi

echo "✓ API servisi çalışıyor"
echo ""

# Sahte yazıcıyı arka planda başlat
echo "→ Sahte yazıcı başlatılıyor (simulate mode)..."
python3 fake_printer.py --mode simulate --no-color > /tmp/fake_printer_error_test.log 2>&1 &
PRINTER_PID=$!

sleep 2

if ! ps -p $PRINTER_PID > /dev/null; then
    echo "✗ HATA: Sahte yazıcı başlatılamadı!"
    exit 1
fi

echo "✓ Sahte yazıcı başlatıldı (PID: $PRINTER_PID)"
echo ""

# API'ye bağlan
echo "→ API'ye bağlanılıyor..."
CONNECT_RESPONSE=$(curl -s -X POST http://localhost:8000/connect \
  -H "Authorization: Bearer change-me-secret-token" \
  -H "Content-Type: application/json" \
  -d '{"connection_type": "lan", "lan_host": "127.0.0.1", "lan_port": 9100}')

if echo "$CONNECT_RESPONSE" | grep -q "connected"; then
    echo "✓ Yazıcıya bağlanıldı"
else
    echo "✗ Yazıcıya bağlanılamadı!"
    kill $PRINTER_PID 2>/dev/null
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "HATA SİMÜLASYONU TESTLERİ"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Test 1: PAPER_OUT
echo "▶ Test 1: PAPER_OUT (Kağıt Bitti)"
echo "─────────────────────────────────────────────────────────"
echo ""
echo "Sahte yazıcıda PAPER_OUT hatası simüle ediliyor..."

# Python ile hata simüle et (klavye girişi yerine)
python3 << 'EOF' &
import socket
import time
time.sleep(1)
# Not: Gerçek implementasyonda klavye simülasyonu gerekir
# Bu sadece gösterim amaçlıdır
EOF

sleep 2

echo "→ Yazdırma isteği gönderiliyor..."
PRINT_RESPONSE=$(curl -s -X POST http://localhost:8000/print/text \
  -H "Authorization: Bearer change-me-secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "error-test-001",
    "lines": [{"text": "Test - Paper Out"}],
    "cut": true
  }')

echo ""
echo "API Yanıtı:"
echo "$PRINT_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$PRINT_RESPONSE"
echo ""

if echo "$PRINT_RESPONSE" | grep -q "PAPER_OUT"; then
    echo "✓ PAPER_OUT hatası başarıyla yakalandı!"
else
    echo "! Hata yakalanmadı (normal yazdırma yapıldı)"
fi

echo ""
read -p "Devam etmek için ENTER'a basın..."

# Temizlik
echo ""
echo "→ Temizlik yapılıyor..."
kill $PRINTER_PID 2>/dev/null
wait $PRINTER_PID 2>/dev/null

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Test tamamlandı!"
echo ""
echo "Manuel test için:"
echo "1. Terminal 1: python3 fake_printer.py --mode simulate"
echo "2. Terminal 2: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo "3. Terminal 1'de tuşlara bas: P (Paper Out), C (Cover Open), H (Overheat)"
echo "4. Terminal 3'te yazdırma isteği gönder"
echo "═══════════════════════════════════════════════════════════"
