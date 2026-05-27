#!/bin/bash
# Tüm Testleri Çalıştır

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     Sahte Termal Yazıcı - Tüm Testler                    ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Test sonuçlarını sakla
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Test 1: Basit Bağlantı
echo ""
echo "▶ Test 1/3: Basit Bağlantı Testi"
echo "─────────────────────────────────────────────────────────"
if bash test_1_simple_connection.sh; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo "✓ Test 1 BAŞARILI"
else
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo "✗ Test 1 BAŞARISIZ"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo ""
echo "Sonraki teste geçmek için 3 saniye bekleniyor..."
sleep 3

# Test 2: Status Query
echo ""
echo "▶ Test 2/3: Status Query Testi"
echo "─────────────────────────────────────────────────────────"
if bash test_2_status_query.sh; then
    PASSED_TESTS=$((PASSED_TESTS + 1))
    echo "✓ Test 2 BAŞARILI"
else
    FAILED_TESTS=$((FAILED_TESTS + 1))
    echo "✗ Test 2 BAŞARISIZ"
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

echo ""
echo "Sonraki teste geçmek için 3 saniye bekleniyor..."
sleep 3

# Test 3: API Entegrasyon (opsiyonel)
echo ""
echo "▶ Test 3/3: API Entegrasyon Testi (Opsiyonel)"
echo "─────────────────────────────────────────────────────────"
echo "Bu test API servisinin çalışmasını gerektirir."
read -p "API entegrasyon testini çalıştırmak istiyor musunuz? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    if bash test_3_api_integration.sh; then
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo "✓ Test 3 BAŞARILI"
    else
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "✗ Test 3 BAŞARISIZ"
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
else
    echo "Test 3 atlandı."
fi

# Özet
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                    TEST ÖZETI                             ║"
echo "╠═══════════════════════════════════════════════════════════╣"
echo "║  Toplam Test:    $TOTAL_TESTS                                          ║"
echo "║  Başarılı:       $PASSED_TESTS                                          ║"
echo "║  Başarısız:      $FAILED_TESTS                                          ║"
echo "╚═══════════════════════════════════════════════════════════╝"

if [ $FAILED_TESTS -eq 0 ]; then
    echo ""
    echo "🎉 Tüm testler başarıyla tamamlandı!"
    exit 0
else
    echo ""
    echo "⚠️  Bazı testler başarısız oldu."
    exit 1
fi
