"""
Endpoint açıklamaları için çoklu dil desteği
"""
from typing import Dict, Any

# Endpoint açıklamaları çevirileri
ENDPOINT_TRANSLATIONS = {
    "logs": {
        "get_logs": {
            "tr": {
                "summary": "Log Kayıtlarını Listele",
                "description": """
Tüm yazdırma işlemlerinin ve sistem olaylarının log kayıtlarını sayfalı olarak döner.

## Filtreleme Seçenekleri

### Duruma Göre Filtreleme (status)
- **done**: Başarıyla tamamlanan işlemler
- **failed**: Başarısız olan işlemler
- **info**: Bilgilendirme logları

### İşleme Göre Filtreleme (op)
İşlem türüne göre filtreleme yapabilirsiniz:
- `print_text`: Metin yazdırma
- `print_image`: Görsel yazdırma
- `print_qr`: QR kod yazdırma
- `print_smart`: Akıllı yazdırma
- `connect`: Bağlantı kurma
- `disconnect`: Bağlantı kesme

## Sayfalama
- **page**: Sayfa numarası (varsayılan: 1)
- **page_size**: Sayfa başına kayıt sayısı (varsayılan: 100, maksimum: 1000)

## Log Formatı
Her log kaydı şu bilgileri içerir:
- **ts**: Zaman damgası (ISO-8601 formatında)
- **op**: İşlem adı
- **conn**: Bağlantı tipi (usb/lan)
- **job_id**: İş kimliği
- **status**: İşlem durumu
- **error**: Hata detayı (varsa)

## Kullanım Senaryoları
- Hata ayıklama ve sorun giderme
- İşlem geçmişi takibi
- Performans analizi
- Denetim (audit) kayıtları
- Raporlama ve istatistik
                """,
                "response_description": "Sayfalı log kayıtları"
            },
            "en": {
                "summary": "List Log Records",
                "description": """
Returns paginated log records of all print operations and system events.

## Filtering Options

### Filter by Status
- **done**: Successfully completed operations
- **failed**: Failed operations
- **info**: Information logs

### Filter by Operation (op)
You can filter by operation type:
- `print_text`: Text printing
- `print_image`: Image printing
- `print_qr`: QR code printing
- `print_smart`: Smart printing
- `connect`: Connection establishment
- `disconnect`: Connection termination

## Pagination
- **page**: Page number (default: 1)
- **page_size**: Records per page (default: 100, maximum: 1000)

## Log Format
Each log record contains:
- **ts**: Timestamp (ISO-8601 format)
- **op**: Operation name
- **conn**: Connection type (usb/lan)
- **job_id**: Job identifier
- **status**: Operation status
- **error**: Error details (if any)

## Use Cases
- Debugging and troubleshooting
- Operation history tracking
- Performance analysis
- Audit records
- Reporting and statistics
                """,
                "response_description": "Paginated log records"
            },
            "de": {
                "summary": "Protokolleinträge auflisten",
                "description": """
Gibt paginierte Protokolleinträge aller Druckvorgänge und Systemereignisse zurück.

## Filteroptionen

### Nach Status filtern
- **done**: Erfolgreich abgeschlossene Vorgänge
- **failed**: Fehlgeschlagene Vorgänge
- **info**: Informationsprotokolle

### Nach Vorgang filtern (op)
Sie können nach Vorgangstyp filtern:
- `print_text`: Textdruck
- `print_image`: Bilddruck
- `print_qr`: QR-Code-Druck
- `print_smart`: Intelligenter Druck
- `connect`: Verbindungsaufbau
- `disconnect`: Verbindungstrennung

## Paginierung
- **page**: Seitennummer (Standard: 1)
- **page_size**: Einträge pro Seite (Standard: 100, Maximum: 1000)

## Protokollformat
Jeder Protokolleintrag enthält:
- **ts**: Zeitstempel (ISO-8601-Format)
- **op**: Vorgangsname
- **conn**: Verbindungstyp (usb/lan)
- **job_id**: Auftragskennung
- **status**: Vorgangsstatus
- **error**: Fehlerdetails (falls vorhanden)

## Anwendungsfälle
- Fehlersuche und Problemlösung
- Vorgangsverlauf verfolgen
- Leistungsanalyse
- Audit-Aufzeichnungen
- Berichterstattung und Statistik
                """,
                "response_description": "Paginierte Protokolleinträge"
            },
            "fr": {
                "summary": "Lister les enregistrements de journal",
                "description": """
Renvoie les enregistrements de journal paginés de toutes les opérations d'impression et événements système.

## Options de filtrage

### Filtrer par statut
- **done**: Opérations terminées avec succès
- **failed**: Opérations échouées
- **info**: Journaux d'information

### Filtrer par opération (op)
Vous pouvez filtrer par type d'opération:
- `print_text`: Impression de texte
- `print_image`: Impression d'image
- `print_qr`: Impression de code QR
- `print_smart`: Impression intelligente
- `connect`: Établissement de connexion
- `disconnect`: Déconnexion

## Pagination
- **page**: Numéro de page (par défaut: 1)
- **page_size**: Enregistrements par page (par défaut: 100, maximum: 1000)

## Format de journal
Chaque enregistrement de journal contient:
- **ts**: Horodatage (format ISO-8601)
- **op**: Nom de l'opération
- **conn**: Type de connexion (usb/lan)
- **job_id**: Identifiant de tâche
- **status**: Statut de l'opération
- **error**: Détails de l'erreur (le cas échéant)

## Cas d'utilisation
- Débogage et dépannage
- Suivi de l'historique des opérations
- Analyse des performances
- Enregistrements d'audit
- Rapports et statistiques
                """,
                "response_description": "Enregistrements de journal paginés"
            }
        },
        "export_logs": {
            "tr": {
                "summary": "Logları CSV Olarak İndir",
                "description": """
Tüm log kayıtlarını CSV formatında indirir.

## Özellikler
- Tüm log kayıtları tek seferde indirilir
- CSV formatı Excel ve diğer araçlarla uyumludur
- Dosya adı: `printer_logs.csv`

## CSV Sütunları
- Timestamp (Zaman)
- Operation (İşlem)
- Connection (Bağlantı)
- Job ID (İş Kimliği)
- Status (Durum)
- Error Code (Hata Kodu)
- Error Detail (Hata Detayı)

## Kullanım Alanları
- Uzun dönem analiz için veri arşivleme
- Excel'de pivot tablo ve grafik oluşturma
- Harici analiz araçlarına veri aktarımı
- Yedekleme ve raporlama
                """,
                "response_description": "CSV dosyası"
            },
            "en": {
                "summary": "Download Logs as CSV",
                "description": """
Downloads all log records in CSV format.

## Features
- All log records are downloaded at once
- CSV format is compatible with Excel and other tools
- File name: `printer_logs.csv`

## CSV Columns
- Timestamp
- Operation
- Connection
- Job ID
- Status
- Error Code
- Error Detail

## Use Cases
- Data archiving for long-term analysis
- Creating pivot tables and charts in Excel
- Data export to external analysis tools
- Backup and reporting
                """,
                "response_description": "CSV file"
            },
            "de": {
                "summary": "Protokolle als CSV herunterladen",
                "description": """
Lädt alle Protokolleinträge im CSV-Format herunter.

## Funktionen
- Alle Protokolleinträge werden auf einmal heruntergeladen
- CSV-Format ist mit Excel und anderen Tools kompatibel
- Dateiname: `printer_logs.csv`

## CSV-Spalten
- Zeitstempel
- Vorgang
- Verbindung
- Auftrags-ID
- Status
- Fehlercode
- Fehlerdetail

## Anwendungsfälle
- Datenarchivierung für Langzeitanalyse
- Erstellen von Pivot-Tabellen und Diagrammen in Excel
- Datenexport zu externen Analysetools
- Sicherung und Berichterstattung
                """,
                "response_description": "CSV-Datei"
            },
            "fr": {
                "summary": "Télécharger les journaux au format CSV",
                "description": """
Télécharge tous les enregistrements de journal au format CSV.

## Fonctionnalités
- Tous les enregistrements de journal sont téléchargés en une seule fois
- Le format CSV est compatible avec Excel et d'autres outils
- Nom du fichier: `printer_logs.csv`

## Colonnes CSV
- Horodatage
- Opération
- Connexion
- ID de tâche
- Statut
- Code d'erreur
- Détail de l'erreur

## Cas d'utilisation
- Archivage de données pour analyse à long terme
- Création de tableaux croisés dynamiques et de graphiques dans Excel
- Export de données vers des outils d'analyse externes
- Sauvegarde et rapports
                """,
                "response_description": "Fichier CSV"
            }
        },
        "list_failed_jobs": {
            "tr": {
                "summary": "Başarısız İşleri Listele",
                "description": """
Başarısız olan ve yeniden yazdırılmayı bekleyen işlerin listesini döner.

## Ne Zaman Kullanılır?
- Kağıt bitmesi nedeniyle başarısız olan işleri görmek için
- Yazıcı hatası sonrası bekleyen işleri kontrol etmek için
- Yeniden yazdırma işlemi öncesi listeyi görmek için

## Başarısız İş Yönetimi
1. İş başarısız olduğunda otomatik olarak `data/failed_jobs/` klasörüne kaydedilir
2. Bu endpoint ile başarısız işlerin listesini alabilirsiniz
3. `/reprint` endpoint'i ile işi yeniden yazdırabilirsiniz
4. Başarılı yazdırma sonrası iş otomatik olarak listeden silinir

## Dönen Bilgiler
- Job ID listesi
- Her iş için kaydedilme zamanı
- İşin orijinal parametreleri
                """,
                "response_description": "Başarısız iş listesi"
            },
            "en": {
                "summary": "List Failed Jobs",
                "description": """
Returns a list of failed jobs waiting to be reprinted.

## When to Use?
- To see jobs that failed due to paper out
- To check pending jobs after printer error
- To view the list before reprinting

## Failed Job Management
1. When a job fails, it's automatically saved to `data/failed_jobs/` folder
2. Use this endpoint to get the list of failed jobs
3. Use `/reprint` endpoint to reprint the job
4. After successful printing, the job is automatically removed from the list

## Returned Information
- Job ID list
- Save time for each job
- Original parameters of the job
                """,
                "response_description": "Failed job list"
            },
            "de": {
                "summary": "Fehlgeschlagene Aufträge auflisten",
                "description": """
Gibt eine Liste fehlgeschlagener Aufträge zurück, die auf Neudruck warten.

## Wann verwenden?
- Um Aufträge zu sehen, die aufgrund von Papiermangel fehlgeschlagen sind
- Um ausstehende Aufträge nach Druckerfehler zu überprüfen
- Um die Liste vor dem Neudruck anzuzeigen

## Verwaltung fehlgeschlagener Aufträge
1. Wenn ein Auftrag fehlschlägt, wird er automatisch im Ordner `data/failed_jobs/` gespeichert
2. Verwenden Sie diesen Endpunkt, um die Liste fehlgeschlagener Aufträge abzurufen
3. Verwenden Sie den Endpunkt `/reprint`, um den Auftrag neu zu drucken
4. Nach erfolgreichem Druck wird der Auftrag automatisch aus der Liste entfernt

## Zurückgegebene Informationen
- Auftrags-ID-Liste
- Speicherzeit für jeden Auftrag
- Ursprüngliche Parameter des Auftrags
                """,
                "response_description": "Liste fehlgeschlagener Aufträge"
            },
            "fr": {
                "summary": "Lister les tâches échouées",
                "description": """
Renvoie une liste des tâches échouées en attente de réimpression.

## Quand utiliser?
- Pour voir les tâches qui ont échoué en raison d'un manque de papier
- Pour vérifier les tâches en attente après une erreur d'imprimante
- Pour afficher la liste avant la réimpression

## Gestion des tâches échouées
1. Lorsqu'une tâche échoue, elle est automatiquement enregistrée dans le dossier `data/failed_jobs/`
2. Utilisez ce point de terminaison pour obtenir la liste des tâches échouées
3. Utilisez le point de terminaison `/reprint` pour réimprimer la tâche
4. Après une impression réussie, la tâche est automatiquement supprimée de la liste

## Informations renvoyées
- Liste des ID de tâche
- Heure d'enregistrement pour chaque tâche
- Paramètres d'origine de la tâche
                """,
                "response_description": "Liste des tâches échouées"
            }
        }
    },
    "reprint": {
        "reprint": {
            "tr": {
                "summary": "Başarısız İşi Yeniden Yazdır",
                "description": """
Başarısız olan bir yazdırma işini yeniden dener.

## Nasıl Çalışır?

### 1. Otomatik Kaydetme
Bir yazdırma işi başarısız olduğunda (kağıt bitmesi, kapak açık, vb.), iş otomatik olarak `data/failed_jobs/` klasörüne kaydedilir.

### 2. Yeniden Yazdırma
Bu endpoint ile job_id kullanarak başarısız işi yeniden yazdırabilirsiniz. Orijinal parametreler korunur.

### 3. Otomatik Temizlik
Yeniden yazdırma başarılı olursa, iş otomatik olarak başarısız kuyruktan silinir.

## Kullanım Senaryoları

### Kağıt Bitmesi
1. Yazdırma sırasında kağıt biter
2. İş başarısız olarak kaydedilir
3. Kağıt yüklenir
4. Bu endpoint ile iş yeniden yazdırılır

### Kapak Açık
1. Yazdırma sırasında kapak açılır
2. İş başarısız olarak kaydedilir
3. Kapak kapatılır
4. İş yeniden yazdırılır

### Bağlantı Hatası
1. Geçici bağlantı sorunu oluşur
2. İş başarısız olarak kaydedilir
3. Bağlantı düzelir
4. İş yeniden yazdırılır

## Özellikler
- Orijinal iş parametreleri korunur
- Aynı job_id ile tekrar yazdırılır
- Başarılı olursa otomatik temizlenir
- Başarısız olursa kuyrukta kalır

## Dil Desteği
`language` parametresi ile hata mesajlarının dilini değiştirebilirsiniz.
                """,
                "response_description": "Yeniden yazdırma işi başarıyla tamamlandı"
            },
            "en": {
                "summary": "Reprint Failed Job",
                "description": """
Retries a failed print job.

## How It Works?

### 1. Automatic Saving
When a print job fails (paper out, cover open, etc.), the job is automatically saved to `data/failed_jobs/` folder.

### 2. Reprinting
Use this endpoint with job_id to reprint the failed job. Original parameters are preserved.

### 3. Automatic Cleanup
If reprinting succeeds, the job is automatically removed from the failed queue.

## Usage Scenarios

### Paper Out
1. Paper runs out during printing
2. Job is saved as failed
3. Paper is loaded
4. Job is reprinted with this endpoint

### Cover Open
1. Cover opens during printing
2. Job is saved as failed
3. Cover is closed
4. Job is reprinted

### Connection Error
1. Temporary connection issue occurs
2. Job is saved as failed
3. Connection is restored
4. Job is reprinted

## Features
- Original job parameters are preserved
- Reprinted with the same job_id
- Automatically cleaned up if successful
- Remains in queue if failed

## Language Support
You can change the language of error messages with the `language` parameter.
                """,
                "response_description": "Reprint job completed successfully"
            },
            "de": {
                "summary": "Fehlgeschlagenen Auftrag neu drucken",
                "description": """
Wiederholt einen fehlgeschlagenen Druckauftrag.

## Wie funktioniert es?

### 1. Automatisches Speichern
Wenn ein Druckauftrag fehlschlägt (Papier aus, Abdeckung offen usw.), wird der Auftrag automatisch im Ordner `data/failed_jobs/` gespeichert.

### 2. Neudruck
Verwenden Sie diesen Endpunkt mit job_id, um den fehlgeschlagenen Auftrag neu zu drucken. Ursprüngliche Parameter werden beibehalten.

### 3. Automatische Bereinigung
Wenn der Neudruck erfolgreich ist, wird der Auftrag automatisch aus der Fehlerwarteschlange entfernt.

## Verwendungsszenarien

### Papier aus
1. Papier geht während des Druckens aus
2. Auftrag wird als fehlgeschlagen gespeichert
3. Papier wird eingelegt
4. Auftrag wird mit diesem Endpunkt neu gedruckt

### Abdeckung offen
1. Abdeckung öffnet sich während des Druckens
2. Auftrag wird als fehlgeschlagen gespeichert
3. Abdeckung wird geschlossen
4. Auftrag wird neu gedruckt

### Verbindungsfehler
1. Vorübergehendes Verbindungsproblem tritt auf
2. Auftrag wird als fehlgeschlagen gespeichert
3. Verbindung wird wiederhergestellt
4. Auftrag wird neu gedruckt

## Funktionen
- Ursprüngliche Auftragsparameter werden beibehalten
- Neu gedruckt mit derselben job_id
- Automatisch bereinigt bei Erfolg
- Bleibt in der Warteschlange bei Fehler

## Sprachunterstützung
Sie können die Sprache der Fehlermeldungen mit dem Parameter `language` ändern.
                """,
                "response_description": "Neudruckauftrag erfolgreich abgeschlossen"
            },
            "fr": {
                "summary": "Réimprimer une tâche échouée",
                "description": """
Réessaie une tâche d'impression échouée.

## Comment ça marche?

### 1. Sauvegarde automatique
Lorsqu'une tâche d'impression échoue (papier épuisé, couvercle ouvert, etc.), la tâche est automatiquement enregistrée dans le dossier `data/failed_jobs/`.

### 2. Réimpression
Utilisez ce point de terminaison avec job_id pour réimprimer la tâche échouée. Les paramètres d'origine sont conservés.

### 3. Nettoyage automatique
Si la réimpression réussit, la tâche est automatiquement supprimée de la file d'attente des échecs.

## Scénarios d'utilisation

### Papier épuisé
1. Le papier s'épuise pendant l'impression
2. La tâche est enregistrée comme échouée
3. Le papier est chargé
4. La tâche est réimprimée avec ce point de terminaison

### Couvercle ouvert
1. Le couvercle s'ouvre pendant l'impression
2. La tâche est enregistrée comme échouée
3. Le couvercle est fermé
4. La tâche est réimprimée

### Erreur de connexion
1. Un problème de connexion temporaire se produit
2. La tâche est enregistrée comme échouée
3. La connexion est rétablie
4. La tâche est réimprimée

## Fonctionnalités
- Les paramètres d'origine de la tâche sont conservés
- Réimprimé avec le même job_id
- Nettoyé automatiquement en cas de succès
- Reste dans la file d'attente en cas d'échec

## Support linguistique
Vous pouvez changer la langue des messages d'erreur avec le paramètre `language`.
                """,
                "response_description": "Tâche de réimpression terminée avec succès"
            }
        }
    }
}


def get_endpoint_translation(category: str, endpoint: str, lang: str = "tr") -> Dict[str, str]:
    """
    Belirtilen endpoint için çeviriyi döndürür
    
    Args:
        category: Endpoint kategorisi (logs, reprint, vb.)
        endpoint: Endpoint adı
        lang: Dil kodu (tr, en, de, fr)
    
    Returns:
        summary, description ve response_description içeren dict
    """
    try:
        return ENDPOINT_TRANSLATIONS[category][endpoint].get(lang, ENDPOINT_TRANSLATIONS[category][endpoint]["tr"])
    except KeyError:
        # Fallback to Turkish if translation not found
        return {
            "summary": "Endpoint",
            "description": "No description available",
            "response_description": "Response"
        }
