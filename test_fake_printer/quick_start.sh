#!/bin/bash
# Hızlı Başlangıç Scripti

clear

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║     Sahte Termal Yazıcı - Hızlı Başlangıç                ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "Bu script sahte yazıcıyı hızlıca başlatmanıza yardımcı olur."
echo ""

# Mod seçimi
echo "Çalışma modunu seçin:"
echo ""
echo "  1) Simple   - Ham byte verilerini göster (hızlı test)"
echo "  2) Parse    - ESC/POS komutlarını parse et (önerilen)"
echo "  3) Simulate - Tam simülasyon (hata simülasyonu ile)"
echo ""
read -p "Seçiminiz (1-3) [2]: " MODE_CHOICE

case $MODE_CHOICE in
    1)
        MODE="simple"
        ;;
    3)
        MODE="simulate"
        ;;
    *)
        MODE="parse"
        ;;
esac

# Port seçimi
echo ""
read -p "Port numarası [9100]: " PORT_INPUT
PORT=${PORT_INPUT:-9100}

# Encoding seçimi
echo ""
echo "Metin encoding:"
echo "  1) cp857 (Türkçe - önerilen)"
echo "  2) utf-8"
echo "  3) latin-1"
echo ""
read -p "Seçiminiz (1-3) [1]: " ENC_CHOICE

case $ENC_CHOICE in
    2)
        ENCODING="utf-8"
        ;;
    3)
        ENCODING="latin-1"
        ;;
    *)
        ENCODING="cp857"
        ;;
esac

# Log dosyası
echo ""
read -p "Log dosyası oluşturulsun mu? (y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    LOG_FILE="printer_$(date +%Y%m%d_%H%M%S).log"
    LOG_ARG="--log $LOG_FILE"
else
    LOG_ARG=""
fi

# Özet
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "Yapılandırma:"
echo "  Mod:      $MODE"
echo "  Port:     $PORT"
echo "  Encoding: $ENCODING"
if [ -n "$LOG_FILE" ]; then
    echo "  Log:      $LOG_FILE"
fi
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Sahte yazıcı başlatılıyor..."
echo ""

# Yazıcıyı başlat
python3 fake_printer.py --mode $MODE --port $PORT --encoding $ENCODING $LOG_ARG

echo ""
echo "Sahte yazıcı kapatıldı."
