#!/bin/bash
# Test Script 2: Status Query Testi

echo "═══════════════════════════════════════════════════════════"
echo "Test 2: Status Query Testi"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Bu test DLE EOT status query komutunu test eder."
echo ""
read -p "Devam etmek için ENTER'a basın..."

# Sahte yazıcıyı arka planda başlat
echo ""
echo "→ Sahte yazıcı başlatılıyor (simulate mode)..."
python3 fake_printer.py --mode simulate --no-color > /tmp/fake_printer_test2.log 2>&1 &
PRINTER_PID=$!

# Yazıcının başlamasını bekle
sleep 2

# Yazıcının çalıştığını kontrol et
if ! ps -p $PRINTER_PID > /dev/null; then
    echo "✗ HATA: Sahte yazıcı başlatılamadı!"
    cat /tmp/fake_printer_test2.log
    exit 1
fi

echo "✓ Sahte yazıcı başlatıldı (PID: $PRINTER_PID)"

# Python ile status query gönder
echo ""
echo "→ Status query gönderiliyor..."

python3 << 'EOF'
import socket
import sys

try:
    s = socket.socket()
    s.settimeout(5)
    s.connect(('localhost', 9100))
    
    # DLE EOT 1 komutu gönder
    s.send(b'\x10\x04\x01')
    
    # Yanıtı al
    status = s.recv(1)
    
    if len(status) == 1:
        status_byte = status[0]
        print(f"✓ Status byte alındı: 0x{status_byte:02X}")
        
        if status_byte == 0x00:
            print("✓ Yazıcı durumu: Normal (0x00)")
            sys.exit(0)
        else:
            print(f"! Yazıcı durumu: Hata (0x{status_byte:02X})")
            sys.exit(0)
    else:
        print("✗ Status byte alınamadı!")
        sys.exit(1)
    
    s.close()

except Exception as e:
    print(f"✗ Hata: {e}")
    sys.exit(1)
EOF

QUERY_RESULT=$?

# Kısa bir süre bekle
sleep 1

# Log'u kontrol et
echo ""
echo "→ Log kontrol ediliyor..."
if grep -q "STATUS QUERY" /tmp/fake_printer_test2.log; then
    echo "✓ Status query log'da görüldü!"
    echo ""
    echo "Log çıktısı:"
    echo "─────────────────────────────────────────────────────────"
    grep -A 2 "STATUS QUERY" /tmp/fake_printer_test2.log | tail -n 3
    echo "─────────────────────────────────────────────────────────"
fi

# Temizlik
echo ""
echo "→ Temizlik yapılıyor..."
kill $PRINTER_PID 2>/dev/null
wait $PRINTER_PID 2>/dev/null

echo ""
echo "═══════════════════════════════════════════════════════════"
if [ $QUERY_RESULT -eq 0 ]; then
    echo "Test Sonucu: BAŞARILI"
    echo "═══════════════════════════════════════════════════════════"
    exit 0
else
    echo "Test Sonucu: BAŞARISIZ"
    echo "═══════════════════════════════════════════════════════════"
    exit 1
fi
