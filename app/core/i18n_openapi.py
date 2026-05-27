"""
Multi-language OpenAPI documentation generator
"""
from typing import Dict, Any

# Dil çevirileri
TRANSLATIONS = {
    "tr": {
        "title": "Termal Yazıcı Servisi API",
        "description": """# Cashino KP-300 / KP-301H Termal Yazıcı REST API

Profesyonel termal yazıcı yönetimi için eksiksiz REST API servisi.

## Temel Özellikler

### Bağlantı Yönetimi
- **USB Bağlantı**: Plug-and-play USB desteği
- **LAN Bağlantı**: Ağ üzerinden IP/Port ile bağlantı
- **Otomatik Yeniden Bağlanma**: Bağlantı kopması durumunda otomatik deneme

### Yazdırma Yetenekleri
- **Metin Yazdırma**: Formatlanmış metin satırları (kalın, altı çizili, hizalama, font boyutu)
- **Görsel Yazdırma**: PNG/JPEG formatında base64 kodlu görseller
- **QR Kod**: Özelleştirilebilir boyut ve hata düzeltme seviyesi
- **Akıllı Yazdırma**: Yapay zeka destekli otomatik fiş formatı (opsiyonel)

### Sistem Özellikleri
- **Çoklu Dil**: Türkçe, İngilizce, Almanca, Fransızca
- **Detaylı Loglama**: JSON formatında yapılandırılmış loglar
- **Kuyruk Yönetimi**: Başarısız işleri yeniden yazdırma
- **Durum İzleme**: Gerçek zamanlı yazıcı durumu ve metrikler

## Kimlik Doğrulama

Tüm endpoint'ler (sadece `/health` hariç) Bearer token ile korunmaktadır.

## Dil Desteği

Her endpoint `language` parametresi ile dil seçimi yapabilir: `tr`, `en`, `de`, `fr`
""",
        "tags": {
            "Sağlık": "Servis sağlık kontrolü",
            "Durum": "Yazıcı durum bilgileri",
            "Bağlantı": "Yazıcı bağlantı yönetimi",
            "Yazdırma": "Yazdırma işlemleri",
            "Yeniden Yazdır": "Başarısız işleri yeniden yazdırma",
            "Loglar": "Log yönetimi"
        }
    },
    "en": {
        "title": "Thermal Printer Service API",
        "description": """# Cashino KP-300 / KP-301H Thermal Printer REST API

Complete REST API service for professional thermal printer management.

## Key Features

### Connection Management
- **USB Connection**: Plug-and-play USB support
- **LAN Connection**: Network connection via IP/Port
- **Auto Reconnection**: Automatic retry on connection loss

### Printing Capabilities
- **Text Printing**: Formatted text lines (bold, underline, alignment, font size)
- **Image Printing**: Base64 encoded PNG/JPEG images
- **QR Code**: Customizable size and error correction level
- **Smart Printing**: AI-powered automatic receipt format (optional)

### System Features
- **Multi-language**: Turkish, English, German, French
- **Detailed Logging**: Structured logs in JSON format
- **Queue Management**: Reprint failed jobs
- **Status Monitoring**: Real-time printer status and metrics

## Authentication

All endpoints (except `/health`) are protected with Bearer token.

## Language Support

Each endpoint supports `language` parameter for language selection: `tr`, `en`, `de`, `fr`
""",
        "tags": {
            "Sağlık": "Service health check",
            "Durum": "Printer status information",
            "Bağlantı": "Printer connection management",
            "Yazdırma": "Printing operations",
            "Yeniden Yazdır": "Reprint failed jobs",
            "Loglar": "Log management"
        }
    },
    "de": {
        "title": "Thermodrucker-Service-API",
        "description": """# Cashino KP-300 / KP-301H Thermodrucker REST API

Vollständiger REST-API-Service für professionelles Thermodruckermanagement.

## Hauptmerkmale

### Verbindungsverwaltung
- **USB-Verbindung**: Plug-and-Play-USB-Unterstützung
- **LAN-Verbindung**: Netzwerkverbindung über IP/Port
- **Automatische Wiederverbindung**: Automatischer Neuversuch bei Verbindungsverlust

### Druckfunktionen
- **Textdruck**: Formatierte Textzeilen (fett, unterstrichen, Ausrichtung, Schriftgröße)
- **Bilddruck**: Base64-kodierte PNG/JPEG-Bilder
- **QR-Code**: Anpassbare Größe und Fehlerkorrektur
- **Intelligenter Druck**: KI-gestütztes automatisches Belegformat (optional)

### Systemfunktionen
- **Mehrsprachig**: Türkisch, Englisch, Deutsch, Französisch
- **Detaillierte Protokollierung**: Strukturierte Protokolle im JSON-Format
- **Warteschlangenverwaltung**: Fehlgeschlagene Aufträge erneut drucken
- **Statusüberwachung**: Echtzeit-Druckerstatus und Metriken

## Authentifizierung

Alle Endpunkte (außer `/health`) sind mit Bearer-Token geschützt.

## Sprachunterstützung

Jeder Endpunkt unterstützt den Parameter `language` zur Sprachauswahl: `tr`, `en`, `de`, `fr`
""",
        "tags": {
            "Sağlık": "Service-Gesundheitsprüfung",
            "Durum": "Druckerstatusinformationen",
            "Bağlantı": "Druckerverbindungsverwaltung",
            "Yazdırma": "Druckvorgänge",
            "Yeniden Yazdır": "Fehlgeschlagene Aufträge erneut drucken",
            "Loglar": "Protokollverwaltung"
        }
    },
    "fr": {
        "title": "API de service d'imprimante thermique",
        "description": """# API REST d'imprimante thermique Cashino KP-300 / KP-301H

Service API REST complet pour la gestion professionnelle d'imprimantes thermiques.

## Fonctionnalités principales

### Gestion des connexions
- **Connexion USB**: Support USB plug-and-play
- **Connexion LAN**: Connexion réseau via IP/Port
- **Reconnexion automatique**: Nouvelle tentative automatique en cas de perte de connexion

### Capacités d'impression
- **Impression de texte**: Lignes de texte formatées (gras, souligné, alignement, taille de police)
- **Impression d'image**: Images PNG/JPEG encodées en base64
- **Code QR**: Taille et niveau de correction d'erreur personnalisables
- **Impression intelligente**: Format de reçu automatique alimenté par l'IA (optionnel)

### Fonctionnalités système
- **Multilingue**: Turc, anglais, allemand, français
- **Journalisation détaillée**: Journaux structurés au format JSON
- **Gestion de file d'attente**: Réimprimer les travaux échoués
- **Surveillance d'état**: État de l'imprimante et métriques en temps réel

## Authentification

Tous les points de terminaison (sauf `/health`) sont protégés par un jeton Bearer.

## Support linguistique

Chaque point de terminaison prend en charge le paramètre `language` pour la sélection de la langue: `tr`, `en`, `de`, `fr`
""",
        "tags": {
            "Sağlık": "Vérification de l'état du service",
            "Durum": "Informations sur l'état de l'imprimante",
            "Bağlantı": "Gestion de la connexion de l'imprimante",
            "Yazdırma": "Opérations d'impression",
            "Yeniden Yazdır": "Réimprimer les travaux échoués",
            "Loglar": "Gestion des journaux"
        }
    }
}


def get_translated_openapi(lang: str = "tr") -> Dict[str, Any]:
    """
    OpenAPI spec'i belirtilen dile göre döndürür
    """
    trans = TRANSLATIONS.get(lang, TRANSLATIONS["tr"])
    
    return {
        "title": trans["title"],
        "description": trans["description"],
        "tags": trans["tags"]
    }
