"""
Endpoint açıklamaları için çoklu dil desteği
Path ve Method bazlı temiz çeviri sistemi
"""
from typing import Dict, Optional

# Path ve Method bazlı çeviri sözlüğü
PATH_TRANSLATIONS = {
    "/health": {
        "get": {
            "tr": {
                "summary": "Servis Sağlık Kontrolü",
                "description": "Servisin genel sağlık durumunu döner. Docker, Kubernetes ve diğer orkestrasyon araçları için health check endpoint'i.",
                "response_description": "Servis sağlık durumu"
            },
            "en": {
                "summary": "Service Health Check",
                "description": "Returns the overall health status of the service. Health check endpoint for Docker, Kubernetes and other orchestration tools.",
                "response_description": "Service health status"
            },
            "de": {
                "summary": "Service-Gesundheitsprüfung",
                "description": "Gibt den allgemeinen Gesundheitszustand des Dienstes zurück. Health-Check-Endpunkt für Docker, Kubernetes und andere Orchestrierungstools.",
                "response_description": "Service-Gesundheitsstatus"
            },
            "fr": {
                "summary": "Vérification de l'état du service",
                "description": "Renvoie l'état de santé général du service. Point de terminaison de vérification de l'état pour Docker, Kubernetes et autres outils d'orchestration.",
                "response_description": "État de santé du service"
            }
        }
    },
    "/status": {
        "get": {
            "tr": {
                "summary": "Yazıcı Durumunu Sorgula",
                "description": "Yazıcının anlık durumunu ve sistem bilgilerini döner.",
                "response_description": "Yazıcı durum bilgileri"
            },
            "en": {
                "summary": "Query Printer Status",
                "description": "Returns the current status and system information of the printer.",
                "response_description": "Printer status information"
            },
            "de": {
                "summary": "Druckerstatus abfragen",
                "description": "Gibt den aktuellen Status und Systeminformationen des Druckers zurück.",
                "response_description": "Druckerstatusinformationen"
            },
            "fr": {
                "summary": "Interroger l'état de l'imprimante",
                "description": "Renvoie l'état actuel et les informations système de l'imprimante.",
                "response_description": "Informations sur l'état de l'imprimante"
            }
        }
    },
    "/connect": {
        "post": {
            "tr": {
                "summary": "Yazıcıya Bağlan",
                "description": "Termal yazıcıya USB veya LAN üzerinden bağlantı kurar.",
                "response_description": "Bağlantı başarıyla kuruldu"
            },
            "en": {
                "summary": "Connect to Printer",
                "description": "Establishes connection to the thermal printer via USB or LAN.",
                "response_description": "Connection established successfully"
            },
            "de": {
                "summary": "Mit Drucker verbinden",
                "description": "Stellt eine Verbindung zum Thermodrucker über USB oder LAN her.",
                "response_description": "Verbindung erfolgreich hergestellt"
            },
            "fr": {
                "summary": "Connecter à l'imprimante",
                "description": "Établit une connexion à l'imprimante thermique via USB ou LAN.",
                "response_description": "Connexion établie avec succès"
            }
        }
    },
    "/connect/disconnect": {
        "post": {
            "tr": {
                "summary": "Bağlantıyı Kes",
                "description": "Yazıcı ile olan aktif bağlantıyı güvenli bir şekilde sonlandırır.",
                "response_description": "Bağlantı başarıyla kesildi"
            },
            "en": {
                "summary": "Disconnect",
                "description": "Safely terminates the active connection with the printer.",
                "response_description": "Connection terminated successfully"
            },
            "de": {
                "summary": "Verbindung trennen",
                "description": "Beendet die aktive Verbindung mit dem Drucker sicher.",
                "response_description": "Verbindung erfolgreich getrennt"
            },
            "fr": {
                "summary": "Déconnecter",
                "description": "Termine en toute sécurité la connexion active avec l'imprimante.",
                "response_description": "Connexion terminée avec succès"
            }
        }
    },
    "/print/text": {
        "post": {
            "tr": {
                "summary": "Metin Yazdır",
                "description": "Formatlanmış metin satırları yazdırır (kalın, altı çizili, hizalama, font boyutu).",
                "response_description": "Yazdırma işi kuyruğa alındı"
            },
            "en": {
                "summary": "Print Text",
                "description": "Prints formatted text lines (bold, underline, alignment, font size).",
                "response_description": "Print job queued"
            },
            "de": {
                "summary": "Text drucken",
                "description": "Druckt formatierte Textzeilen (fett, unterstrichen, Ausrichtung, Schriftgröße).",
                "response_description": "Druckauftrag in Warteschlange"
            },
            "fr": {
                "summary": "Imprimer du texte",
                "description": "Imprime des lignes de texte formatées (gras, souligné, alignement, taille de police).",
                "response_description": "Tâche d'impression mise en file d'attente"
            }
        }
    },
    "/print/image": {
        "post": {
            "tr": {
                "summary": "Görsel Yazdır",
                "description": "PNG/JPEG formatında base64 kodlu görselleri yazdırır.",
                "response_description": "Görsel yazdırma işi kuyruğa alındı"
            },
            "en": {
                "summary": "Print Image",
                "description": "Prints base64 encoded images in PNG/JPEG format.",
                "response_description": "Image print job queued"
            },
            "de": {
                "summary": "Bild drucken",
                "description": "Druckt base64-kodierte Bilder im PNG/JPEG-Format.",
                "response_description": "Bilddruckauftrag in Warteschlange"
            },
            "fr": {
                "summary": "Imprimer une image",
                "description": "Imprime des images encodées en base64 au format PNG/JPEG.",
                "response_description": "Tâche d'impression d'image mise en file d'attente"
            }
        }
    },
    "/print/qr": {
        "post": {
            "tr": {
                "summary": "QR Kod Yazdır",
                "description": "Özelleştirilebilir boyut ve hata düzeltme seviyesi ile QR kod yazdırır.",
                "response_description": "QR kod yazdırma işi kuyruğa alındı"
            },
            "en": {
                "summary": "Print QR Code",
                "description": "Prints QR code with customizable size and error correction level.",
                "response_description": "QR code print job queued"
            },
            "de": {
                "summary": "QR-Code drucken",
                "description": "Druckt QR-Code mit anpassbarer Größe und Fehlerkorrektur.",
                "response_description": "QR-Code-Druckauftrag in Warteschlange"
            },
            "fr": {
                "summary": "Imprimer un code QR",
                "description": "Imprime un code QR avec une taille et un niveau de correction d'erreur personnalisables.",
                "response_description": "Tâche d'impression de code QR mise en file d'attente"
            }
        }
    },
    "/print/smart": {
        "post": {
            "tr": {
                "summary": "Akıllı Yazdırma (Yapay Zeka)",
                "description": (
                    "Serbest metin girin, yapay zeka fiş tasarımını kendisi yapsın.\n\n"
                    "**`prompt`** alanına ne yazdırmak istediğinizi Türkçe olarak anlatın — "
                    "ürünler, fiyatlar, makine ID, tarih, kasiyer adı gibi. "
                    "AI başlığı, hizalamayı, ayraçları ve footer'ı otomatik belirler.\n\n"
                    "**Örnek:**\n```\n"
                    "Kafe fişi — 2 filtre kahve 90₺, 1 su 15₺, toplam 105₺. Kasiyer: Ayşe.\n"
                    "```\n\n"
                    "> ⚠️ Bu özellik `LLM_ENABLED=true` ve geçerli bir API anahtarı gerektirir. "
                    "Devre dışıysa metin serbest format olarak yazdırılır."
                ),
                "response_description": "Akıllı yazdırma işi kuyruğa alındı"
            },
            "en": {
                "summary": "Smart Printing (AI)",
                "description": (
                    "Write a plain-text description — AI designs the receipt layout automatically.\n\n"
                    "Describe what you want in the **`prompt`** field: products, prices, machine ID, "
                    "cashier name, date, totals. The AI decides the title, alignment, separators and footer.\n\n"
                    "**Example:**\n```\n"
                    "Cafe receipt — 2 filter coffee £4.50, 1 water £1.20, total £5.70. Cashier: Emma.\n"
                    "```\n\n"
                    "> ⚠️ Requires `LLM_ENABLED=true` and a valid API key. "
                    "If disabled, the text is formatted as a plain receipt."
                ),
                "response_description": "Smart print job queued"
            },
            "de": {
                "summary": "Intelligenter Druck (KI)",
                "description": (
                    "Freitext eingeben — die KI gestaltet das Beleglayout automatisch.\n\n"
                    "Beschreiben Sie im Feld **`prompt`** was gedruckt werden soll: Produkte, "
                    "Preise, Maschinen-ID, Kassierer, Datum. Die KI bestimmt Titel, Ausrichtung, "
                    "Trennzeichen und Fußzeile.\n\n"
                    "**Beispiel:**\n```\n"
                    "Café-Beleg — 2 Filterkaffee 9€, 1 Wasser 2€, Gesamt 11€. Kassierer: Hans.\n"
                    "```\n\n"
                    "> ⚠️ Erfordert `LLM_ENABLED=true` und einen gültigen API-Schlüssel."
                ),
                "response_description": "Intelligenter Druckauftrag in Warteschlange"
            },
            "fr": {
                "summary": "Impression intelligente (IA)",
                "description": (
                    "Saisissez un texte libre — l'IA conçoit automatiquement la mise en page du reçu.\n\n"
                    "Décrivez dans le champ **`prompt`** ce que vous souhaitez imprimer : produits, "
                    "prix, ID machine, caissier, date. L'IA détermine le titre, l'alignement, "
                    "les séparateurs et le pied de page.\n\n"
                    "**Exemple:**\n```\n"
                    "Reçu café — 2 cafés filtre 9€, 1 eau 2€, total 11€. Caissière: Sophie.\n"
                    "```\n\n"
                    "> ⚠️ Nécessite `LLM_ENABLED=true` et une clé API valide."
                ),
                "response_description": "Tâche d'impression intelligente mise en file d'attente"
            }
        }
    },
    "/reprint": {
        "post": {
            "tr": {
                "summary": "Başarısız İşi Yeniden Yazdır",
                "description": "Başarısız olan bir yazdırma işini yeniden dener. Orijinal parametreler korunur.",
                "response_description": "Yeniden yazdırma işi başarıyla tamamlandı"
            },
            "en": {
                "summary": "Reprint Failed Job",
                "description": "Retries a failed print job. Original parameters are preserved.",
                "response_description": "Reprint job completed successfully"
            },
            "de": {
                "summary": "Fehlgeschlagenen Auftrag neu drucken",
                "description": "Wiederholt einen fehlgeschlagenen Druckauftrag. Ursprüngliche Parameter werden beibehalten.",
                "response_description": "Neudruckauftrag erfolgreich abgeschlossen"
            },
            "fr": {
                "summary": "Réimprimer une tâche échouée",
                "description": "Réessaie une tâche d'impression échouée. Les paramètres d'origine sont conservés.",
                "response_description": "Tâche de réimpression terminée avec succès"
            }
        }
    },
    "/logs": {
        "get": {
            "tr": {
                "summary": "Log Kayıtlarını Listele",
                "description": "Tüm yazdırma işlemlerinin ve sistem olaylarının log kayıtlarını sayfalı olarak döner.",
                "response_description": "Sayfalı log kayıtları"
            },
            "en": {
                "summary": "List Log Records",
                "description": "Returns paginated log records of all print operations and system events.",
                "response_description": "Paginated log records"
            },
            "de": {
                "summary": "Protokolleinträge auflisten",
                "description": "Gibt paginierte Protokolleinträge aller Druckvorgänge und Systemereignisse zurück.",
                "response_description": "Paginierte Protokolleinträge"
            },
            "fr": {
                "summary": "Lister les enregistrements de journal",
                "description": "Renvoie les enregistrements de journal paginés de toutes les opérations d'impression et événements système.",
                "response_description": "Enregistrements de journal paginés"
            }
        }
    },
    "/logs/export": {
        "get": {
            "tr": {
                "summary": "Logları CSV Olarak İndir",
                "description": "Tüm log kayıtlarını CSV formatında indirir.",
                "response_description": "CSV dosyası"
            },
            "en": {
                "summary": "Download Logs as CSV",
                "description": "Downloads all log records in CSV format.",
                "response_description": "CSV file"
            },
            "de": {
                "summary": "Protokolle als CSV herunterladen",
                "description": "Lädt alle Protokolleinträge im CSV-Format herunter.",
                "response_description": "CSV-Datei"
            },
            "fr": {
                "summary": "Télécharger les journaux au format CSV",
                "description": "Télécharge tous les enregistrements de journal au format CSV.",
                "response_description": "Fichier CSV"
            }
        }
    },
    "/print/aco": {
        "post": {
            "tr": {
                "summary": "ACO Recycling Ödül Fişi Yazdır",
                "description": "ACO Recycling geri dönüşüm makinesi için standart ödül fişi: MachineID, tarih, ödül miktarı, ürün tablosu ve QR kod.",
                "response_description": "ACO fişi başarıyla yazdırıldı"
            },
            "en": {
                "summary": "Print ACO Recycling Reward Receipt",
                "description": "Prints standard reward receipt for ACO Recycling reverse vending machine: MachineID, date, reward amount, product table and QR code.",
                "response_description": "ACO receipt printed successfully"
            },
            "de": {
                "summary": "ACO Recycling Belohnung Bon drucken",
                "description": "Druckt Standard-Belohnungsbeleg für ACO Recycling Rücknahmeautomat: MaschinenID, Datum, Belohnungsbetrag, Produkttabelle und QR-Code.",
                "response_description": "ACO-Beleg erfolgreich gedruckt"
            },
            "fr": {
                "summary": "Imprimer le reçu de récompense ACO Recycling",
                "description": "Imprime le reçu de récompense standard pour la machine de collecte ACO Recycling : ID machine, date, montant de récompense, tableau de produits et code QR.",
                "response_description": "Reçu ACO imprimé avec succès"
            }
        }
    },
    "/paper": {
        "get": {
            "tr": {
                "summary": "Rulo Durumunu Sorgula",
                "description": "Kağıt rulo kullanım tahminini döner. Tüm değerler tahminidir.",
                "response_description": "Rulo durum bilgileri"
            },
            "en": {
                "summary": "Query Roll Status",
                "description": "Returns paper roll usage estimate. All values are estimates.",
                "response_description": "Roll status information"
            },
            "de": {
                "summary": "Rollenstatus abfragen",
                "description": "Gibt eine Schätzung des Papierrollenverbrauchs zurück. Alle Werte sind Schätzungen.",
                "response_description": "Rollenstatusinformationen"
            },
            "fr": {
                "summary": "Interroger l'état du rouleau",
                "description": "Renvoie une estimation de l'utilisation du rouleau de papier. Toutes les valeurs sont des estimations.",
                "response_description": "Informations sur l'état du rouleau"
            }
        }
    },
    "/paper/reset": {
        "post": {
            "tr": {
                "summary": "Yeni Rulo Sıfırla",
                "description": "Yeni rulo takıldığında sayacı sıfırlar.",
                "response_description": "Rulo başarıyla sıfırlandı"
            },
            "en": {
                "summary": "Reset New Roll",
                "description": "Resets the counter when a new roll is loaded.",
                "response_description": "Roll reset successfully"
            },
            "de": {
                "summary": "Neue Rolle zurücksetzen",
                "description": "Setzt den Zähler zurück, wenn eine neue Rolle eingelegt wird.",
                "response_description": "Rolle erfolgreich zurückgesetzt"
            },
            "fr": {
                "summary": "Réinitialiser nouveau rouleau",
                "description": "Réinitialise le compteur lorsqu'un nouveau rouleau est chargé.",
                "response_description": "Rouleau réinitialisé avec succès"
            }
        }
    },
    "/logs/failed": {
        "get": {
            "tr": {
                "summary": "Başarısız İşleri Listele",
                "description": "Başarısız olan ve yeniden yazdırılmayı bekleyen işlerin listesini döner.",
                "response_description": "Başarısız iş listesi"
            },
            "en": {
                "summary": "List Failed Jobs",
                "description": "Returns a list of failed jobs waiting to be reprinted.",
                "response_description": "Failed job list"
            },
            "de": {
                "summary": "Fehlgeschlagene Aufträge auflisten",
                "description": "Gibt eine Liste fehlgeschlagener Aufträge zurück, die auf Neudruck warten.",
                "response_description": "Liste fehlgeschlagener Aufträge"
            },
            "fr": {
                "summary": "Lister les tâches échouées",
                "description": "Renvoie une liste des tâches échouées en attente de réimpression.",
                "response_description": "Liste des tâches échouées"
            }
        }
    }
}


def get_translation_by_path(path: str, method: str, lang: str = "tr") -> Optional[Dict[str, str]]:
    """
    Belirtilen path ve method (get/post) için çeviriyi döndürür.
    
    Args:
        path: Endpoint yolu (örn: "/logs", "/connect")
        method: HTTP metodu (get, post, put, delete, patch)
        lang: Dil kodu (tr, en, de, fr)
    
    Returns:
        summary, description ve response_description içeren dict veya None
    
    Example:
        >>> get_translation_by_path("/logs", "get", "en")
        {'summary': 'List Log Records', 'description': '...', 'response_description': '...'}
    """
    try:
        return PATH_TRANSLATIONS[path][method].get(lang, PATH_TRANSLATIONS[path][method]["tr"])
    except KeyError:
        return None
