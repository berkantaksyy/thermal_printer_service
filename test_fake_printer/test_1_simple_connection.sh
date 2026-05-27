#!/bin/bash
# Test Script 1: Basit Bağlantı Testi

echo "═══════════════════════════════════════════════════════════"
echo "Test 1: Basit Bağlantı Testi"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Bu test sahte yazıcının temel bağlantı işlevselliğini kontrol eder."
echo ""
echo "Adımlar:"
echo "1. Sahte yazıcı başlatılacak (simple mode)"
echo "2. Test mesajı gönderilecek"
echo "3. Sonuç kontrol edilecek"
echo ""
read -p "Devam etmek için ENTER'a basın..."

# Sahte yazıcıyı arka planda başlat
echo ""
echo "→ Sahte yazıcı başlatılıyor..."
python3 fake_printer.py --mode simple --no-color > /tmp/fake_printer_test1.log 2>&1 &
PRINTER_PID=$!

# Yazıcının başlamasını bekle
sleep 2

# Yazıcının çalıştığını kontrol et
if ! ps -p $PRINTER_PID > /dev/null; then
    echo "✗ HATA: Sahte yazıcı başlatılamadı!"
    cat /tmp/fake_printer_test1.log
    exit 1
fi

echo "✓ Sahte yazıcı başlatıldı (PID: $PRINTER_PID)"

# Test mesajı gönder
echo ""
echo "→ Test mesajı gönderiliyor..."
echo "Hello Printer!" | nc localhost 9100 2>/dev/null

# Kısa bir süre bekle
sleep 1

# Sonuçları kontrol et
echo ""
echo "→ Sonuçlar kontrol ediliyor..."
if grep -q "RECV" /tmp/fake_printer_test1.log; then
    echo "✓ Test mesajı alındı!"
    echo ""
    echo "Log çıktısı:"
    echo "─────────────────────────────────────────────────────────"
    tail -n 5 /tmp/fake_printer_test1.log
    echo "─────────────────────────────────────────────────────────"
    TEST_RESULT="BAŞARILI"
else
    echo "✗ Test mesajı alınamadı!"
    TEST_RESULT="BAŞARISIZ"
fi

# Temizlik
echo ""
echo "→ Temizlik yapılıyor..."
kill $PRINTER_PID 2>/dev/null
wait $PRINTER_PID 2>/dev/null

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Test Sonucu: $TEST_RESULT"
echo "═══════════════════════════════════════════════════════════"

if [ "$TEST_RESULT" = "BAŞARILI" ]; then
    exit 0
else
    exit 1
fi
