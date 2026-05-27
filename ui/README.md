# 🖥️ ui/ — Web Dashboard

<div align="center">

[![HTML5](https://img.shields.io/badge/HTML5-Single%20File-E34F26?style=flat-square&logo=html5)](index.html)
[![JavaScript](https://img.shields.io/badge/JavaScript-Vanilla-F7DF1E?style=flat-square&logo=javascript)](js/)
[![i18n](https://img.shields.io/badge/i18n-TR%20%7C%20EN%20%7C%20DE%20%7C%20FR-blueviolet?style=flat-square)](i18n/)
[![GitHub Pages](https://img.shields.io/badge/GitHub%20Pages-Ready-222222?style=flat-square&logo=github)](.)

[🇹🇷 Türkçe](#türkçe) · [🇬🇧 English](#english) · [🇩🇪 Deutsch](#deutsch) · [🇫🇷 Français](#français)

</div>

---

<a id="türkçe"></a>

## 🇹🇷 Türkçe

### Genel Bakış

```
ui/
├── index.html         # Ana dashboard sayfası
├── js/
│   ├── app.js         # Ana uygulama mantığı (tüm UI etkileşimleri)
│   ├── api.js         # API istek modülü (fetch wrapper)
│   ├── i18n.js        # Çok dil desteği motoru
│   └── components.js  # Yeniden kullanılabilir UI bileşenleri
├── css/
│   ├── theme.css      # Renk sistemi, CSS değişkenleri
│   ├── layout.css     # Izgara ve sayfa düzeni
│   └── components.css # Buton, form, kart stilleri
└── i18n/
    ├── tr.json        # Türkçe çeviriler (varsayılan)
    ├── en.json        # İngilizce çeviriler
    ├── de.json        # Almanca çeviriler
    └── fr.json        # Fransızca çeviriler
```

### Açılış

Servis çalışırken tarayıcıda açın:
```
http://localhost:8000/ui
```

veya Docker ile:
```
http://localhost:8000/ui
```

---

### Dashboard Bölümleri

#### 1. 🔌 Bağlantı Paneli
Yazıcıya USB veya LAN üzerinden bağlanmayı sağlar.

- **USB modu**: Vendor ID / Product ID ile direkt bağlanır
- **LAN modu**: IP adresi + Port (9100) ile TCP bağlantısı
- **Bağlantı durumu**: Anlık güncellenen durum göstergesi (yeşil/kırmızı)
- **Otomatik yeniden bağlanma**: Bağlantı koptuğunda otomatik deneme

> 📸 Ekran görüntüsü: `docs/screenshots/02-dashboard-connection.png`

---

#### 2. 🖨️ Metin Yazdırma
Satır bazlı formatlı metin yazdırır.

- Birden fazla satır eklenebilir
- Her satır için: **kalın**, **hizalama** (sol/orta/sağ), **yazı boyutu** (normal/çift)
- `job_id` alanı opsiyoneldir; boş bırakılırsa UUID otomatik üretilir
- Kağıt kesme seçeneği (`cut: true/false`)

> 📸 Ekran görüntüsü: `docs/screenshots/03-dashboard-print-text.png`

---

#### 3. 📷 QR Kod Yazdırma
Metin veya URL'den QR kod oluşturup yazdırır.

- **Boyut**: 1-10 arası (varsayılan 6)
- **Hata düzeltme**: L / M / Q / H
- **Hizalama**: sol / orta / sağ
- **Etiket**: QR kodun altına opsiyonel metin

> 📸 Ekran görüntüsü: `docs/screenshots/04-dashboard-print-qr.png`

---

#### 4. ♻️ ACO Recycling Ödül Fişi
Geri dönüşüm makineleri için özel fiş yazdırma formu.

- **Makine ID**: Geri dönüşüm makinesi kimliği
- **Ödül Miktarı**: Müşteriye verilecek ödül (TL cinsinden)
- **Ürün sayaçları**: Cam 🫙 / Plastik ♻️ / Metal 🥫 / Tetrapak 🧃
- **QR Kod verisi**: Opsiyonel doğrulama QR kodu
- **Şablon seçimi**: Farklı fiş şablonları

Önizleme butonu ile fiş çıktısını yazdırmadan görebilirsiniz.

> 📸 Ekran görüntüsü: `docs/screenshots/05-dashboard-aco-recycling.png`

---

#### 5. 📊 Log Görüntüleyici
Tüm yazdırma işlemlerinin geçmişini gösterir.

- **Filtreleme**: Tümü / Sadece Hatalar / Sadece Başarılı
- **Sayfalama**: 100'er kayıt
- **CSV Dışa Aktarma**: Tüm logları `.csv` olarak indir
- **Yeniden Baskı**: Başarısız işleri tekrar yazdır

> 📸 Ekran görüntüsü: `docs/screenshots/06-dashboard-logs.png`

---

#### 6. 🗞️ Kağıt Rulo Takibi
Yazıcıdaki kağıt rulo durumunu izler ve tahmin yapar.

- **Kalan metre**: Tahmini kalan kağıt uzunluğu
- **Kalan baskı sayısı**: Ortalama kullanıma göre tahmini baskı
- **Doluluk çubuğu**: Görsel gösterge (kırmızı = kritik)
- **Yeni Rulo Taktım**: Sayacı sıfırla butonu

> 📸 Ekran görüntüsü: `docs/screenshots/07-dashboard-paper-roll.png`

---

#### 7. ⚙️ Ayarlar
API bağlantı ve görünüm ayarları.

- **API URL**: Servis adresi (varsayılan: `http://localhost:8000`)
- **Bearer Token**: Kimlik doğrulama tokeni
- **Dil Seçimi**: TR / EN / DE / FR
- **Yazıcı Mesaj Dili**: API yanıt dilini ayarla

---

### Dil Sistemi (i18n)

Dashboard tam 4 dil desteğine sahiptir: Türkçe, İngilizce, Almanca, Fransızca.

#### Nasıl Çalışır?

```
ui/i18n/tr.json
ui/i18n/en.json
ui/i18n/de.json
ui/i18n/fr.json
```

`js/i18n.js` modülü seçili dil dosyasını yükler ve `data-i18n` attribute'u olan tüm HTML elementlerini çevirir:

```html
<!-- HTML'de -->
<span data-i18n="aco.title">♻️ ACO Recycling</span>
<option value="all" data-i18n="logs.filter.all">Tümü</option>
```

```javascript
// i18n.js içinde
i18n.t('aco.title')        // → "♻️ ACO Recycling" (TR)
i18n.t('logs.filter.all')  // → "All" (EN)
```

#### Yeni Dil Ekleme

1. `ui/i18n/` klasörüne `{lang}.json` dosyası ekleyin (mevcut dosyaları örnek alın)
2. `js/i18n.js` içindeki dil listesine ekleyin
3. `index.html` içindeki dil seçici menüye ekleyin
4. `app/i18n/{lang}.json` dosyasını da oluşturun (backend yanıtları için)

#### i18n Anahtar Yapısı

```json
{
  "nav": { "title": "Termal Yazıcı Servisi" },
  "connection": {
    "title": "Bağlantı",
    "connect": "Bağlan",
    "disconnect": "Bağlantıyı Kes"
  },
  "print": {
    "text": { "title": "Metin Yazdır", "addLine": "Satır Ekle" },
    "qr": { "title": "QR Kod Yazdır" },
    "image": { "title": "Görsel Yazdır" }
  },
  "aco": {
    "title": "ACO Recycling Ödül Fişi",
    "machine_id": "Makine ID",
    "reward_amount": "Ödül Miktarı"
  },
  "paper": {
    "section_header": "RULO DURUMU",
    "remaining_m": "m kaldı",
    "prints_remaining": "baskı kaldı"
  },
  "logs": {
    "filter": {
      "all": "Tümü",
      "failed": "❌ Sadece Hatalar",
      "done": "✅ Sadece Başarılı"
    }
  },
  "settings": {
    "printerLang": "Yazıcı Mesaj Dili"
  }
}
```

---

### JavaScript Modülleri

#### `js/api.js` — API İstek Modülü

Tüm HTTP isteklerini tek bir yerden yönetir.

```javascript
// Otomatik Bearer token ekleme
// Hata yönetimi
// Zaman aşımı desteği

api.get('/status')
api.post('/print/text', { lines: [...], cut: true })
api.post('/connect', { connection_type: 'lan', lan_host: '...' })
```

Ayarlar `localStorage`'da saklanır: API URL ve Bearer token.

---

#### `js/app.js` — Ana Uygulama

Tüm UI etkileşim mantığını içerir.

Başlıca fonksiyonlar:

| Fonksiyon | Açıklama |
|-----------|----------|
| `init()` | Uygulama başlangıcı, event listener'lar |
| `_loadStatus()` | Yazıcı durumunu getir ve göster (10 saniyede bir otomatik) |
| `_renderPaperStats()` | Kağıt rulo istatistiklerini güncelle |
| `print_text()` | Metin yazdırma formunu işle |
| `print_qr()` | QR kod formunu işle |
| `print_image()` | Görsel yazdırma formunu işle |
| `print_aco()` | ACO fiş formunu işle |
| `showAcoReceiptPreview()` | ACO fiş önizlemesini göster |
| `_loadLogs()` | Logları getir ve tabloya render et |
| `_setLang(lang)` | Dil değiştir ve tüm UI'ı çevir |

---

#### `js/i18n.js` — Çok Dil Motoru

```javascript
// Dili değiştir
i18n.setLang('en')

// Çeviri getir
i18n.t('connection.connect')  // → "Connect"

// Tüm data-i18n elementlerini güncelle
i18n.applyTranslations()
```

Seçilen dil `localStorage`'da saklanır; sayfa yenilendiğinde hatırlanır.

---

#### `js/components.js` — UI Bileşenleri

Yeniden kullanılabilir UI fonksiyonları:

```javascript
ui.success('Yazdırma başarılı!')   // Yeşil toast mesajı
ui.error('Bağlantı hatası!')       // Kırmızı toast mesajı
ui.showModal(content)              // Modal pencere
ui.setLoading(btn, true)           // Buton yükleme durumu
```

---

### CSS Mimarisi

#### `css/theme.css` — Renk Sistemi

CSS custom properties (değişkenleri) ile tema:

```css
:root {
  --color-primary: #667eea;
  --color-success: #48bb78;
  --color-error: #fc8181;
  --color-warning: #f6ad55;
  --color-bg: #f8fafc;
  --color-card: #ffffff;
  --border-radius: 12px;
  --shadow-sm: 0 2px 8px rgba(0,0,0,0.05);
}
```

#### `css/layout.css` — Sayfa Düzeni

CSS Grid ile panel düzeni. Responsive — mobil ekranlarda tek sütuna düşer.

#### `css/components.css` — Bileşen Stilleri

Tüm buton, form, kart, tablo, progress bar ve toast stilleri.

---

### GitHub Pages Dağıtımı

UI, build adımı olmadan doğrudan GitHub Pages'e deploy edilebilir.

#### Seçenek 1: `docs/` klasörüne kopyala

```bash
cp -r ui/ docs/
git add docs/
git commit -m "chore: deploy UI to GitHub Pages"
git push
```

GitHub'da: **Settings → Pages → Source: Deploy from branch → `main` / `docs/`**

#### Seçenek 2: GitHub Actions (Önerilen)

```yaml
# .github/workflows/pages.yml
name: Deploy UI to GitHub Pages
on:
  push:
    branches: [main]
    paths: [ui/**]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/upload-pages-artifact@v3
        with:
          path: ui/
      - uses: actions/deploy-pages@v4
```

#### Demo Modu

GitHub Pages'de barındırılan UI, yerel servise bağlanabilir. Kullanıcı Ayarlar bölümünden API URL'yi `http://localhost:8000` olarak girer. CORS tüm origin'lere açık olduğundan çalışır.

> **Not:** GitHub Pages HTTPS sunar; yerel servis HTTP çalışıyorsa Mixed Content hatası alabilirsiniz. Çözüm: Servisi de HTTPS ile çalıştırın veya `http://` URL'yi tarayıcı izin listesine ekleyin.

---

### Durum Otomatik Yenileme

Dashboard açıkken yazıcı durumu her **10 saniyede** otomatik güncellenir. Elle yenilemek için sayfayı yenileyin veya servis durumu kartına tıklayın.

```javascript
// app.js içinde
setInterval(() => this._loadStatus(), 10_000);
```

---

<a id="english"></a>

<details>
<summary>🇬🇧 English — Click to expand</summary>

## English

### Overview

The UI is a fully client-side web dashboard served at `/ui`. It communicates with the FastAPI backend via REST API calls. No build step required — it's plain HTML + vanilla JavaScript + CSS.

### File Structure

```
ui/
├── index.html         # Main dashboard page
├── js/
│   ├── app.js         # Application logic (all UI interactions)
│   ├── api.js         # API request module (fetch wrapper)
│   ├── i18n.js        # Multi-language engine
│   └── components.js  # Reusable UI components (toast, modal, loading)
├── css/
│   ├── theme.css      # Color system, CSS variables
│   ├── layout.css     # Grid and page layout
│   └── components.css # Button, form, card styles
└── i18n/
    ├── tr.json        # Turkish translations (default)
    ├── en.json        # English translations
    ├── de.json        # German translations
    └── fr.json        # French translations
```

### Access

```
http://localhost:8000/ui
```

### Dashboard Sections

| Section | Description | Screenshot |
|---------|-------------|-----------|
| 🔌 Connection | USB/LAN printer connect, status indicator | `02-dashboard-connection.png` |
| 🖨️ Print Text | Multi-line formatted text with bold/align/size | `03-dashboard-print-text.png` |
| 📷 Print QR | QR code generator with size/error-correction | `04-dashboard-print-qr.png` |
| ♻️ ACO Recycling | Recycling reward receipt form with preview | `05-dashboard-aco-recycling.png` |
| 📊 Logs | Print history with filter, CSV export, reprint | `06-dashboard-logs.png` |
| 🗞️ Paper Roll | Roll estimation, remaining meters, reset | `07-dashboard-paper-roll.png` |
| ⚙️ Settings | API URL, Bearer token, language selection | — |

### i18n System

All 94 UI labels are driven by `data-i18n` attributes:

```html
<span data-i18n="connection.connect">Bağlan</span>
<option value="all" data-i18n="logs.filter.all">Tümü</option>
```

When the language is changed, `i18n.applyTranslations()` updates every element. The selected language persists in `localStorage`.

**Adding a new language:**
1. Create `ui/i18n/{lang}.json` (copy from `en.json`)
2. Add to the language list in `js/i18n.js`
3. Add to the language selector in `index.html`
4. Create `app/i18n/{lang}.json` for backend API responses

### GitHub Pages Deployment

```bash
# Option 1: Copy to docs/
cp -r ui/ docs/
git add docs/ && git commit -m "deploy UI" && git push
# Then: Settings → Pages → branch: main, folder: /docs

# Option 2: GitHub Actions (recommended)
# Create .github/workflows/pages.yml (see Turkish section for full YAML)
```

The UI works in demo mode on GitHub Pages — users configure the API URL in Settings to point to their local service.

### JavaScript Architecture

**`api.js`** — Centralized fetch wrapper. Automatically adds the Bearer token from `localStorage`. Handles timeouts and error parsing.

**`app.js`** — All UI event handlers and state management. Auto-refreshes printer status every 10 seconds. Calls `i18n.t()` for dynamic strings (paper stats, toast messages).

**`i18n.js`** — Language engine. `i18n.t(key)` resolves dot-notation keys from the active language JSON. Falls back to the key string if not found.

**`components.js`** — Toast notifications, modal dialogs, loading button states.

</details>

---

<a id="deutsch"></a>

<details>
<summary>🇩🇪 Deutsch — Klicken zum Aufklappen</summary>

## Deutsch

### Übersicht

Das UI ist ein clientseitiges Web-Dashboard unter `/ui`. Es kommuniziert über REST-API mit dem FastAPI-Backend. Kein Build-Schritt erforderlich — reines HTML + Vanilla JavaScript + CSS.

### Dateistruktur

```
ui/
├── index.html         # Haupt-Dashboard-Seite
├── js/
│   ├── app.js         # Anwendungslogik (alle UI-Interaktionen)
│   ├── api.js         # API-Anfrage-Modul (Fetch-Wrapper)
│   ├── i18n.js        # Mehrsprachigkeits-Engine
│   └── components.js  # Wiederverwendbare UI-Komponenten
├── css/
│   ├── theme.css      # Farbsystem, CSS-Variablen
│   ├── layout.css     # Raster und Seitenlayout
│   └── components.css # Schaltflächen-, Formular-, Kartenstile
└── i18n/
    ├── tr.json / en.json / de.json / fr.json
```

### Dashboard-Abschnitte

| Abschnitt | Beschreibung |
|-----------|--------------|
| 🔌 Verbindung | USB/LAN-Drucker verbinden, Statusanzeige |
| 🖨️ Text drucken | Mehrzeiliger formatierter Text |
| 📷 QR-Code drucken | QR-Code-Generator |
| ♻️ ACO Recycling | Recycling-Bonbeleg-Formular mit Vorschau |
| 📊 Protokolle | Druckhistorie mit Filter und CSV-Export |
| 🗞️ Papierrolle | Rollenüberwachung, verbleibende Meter |
| ⚙️ Einstellungen | API-URL, Token, Sprachauswahl |

### i18n-System

Alle 94 UI-Beschriftungen werden durch `data-i18n`-Attribute gesteuert. Beim Sprachwechsel aktualisiert `i18n.applyTranslations()` alle Elemente. Die gewählte Sprache wird in `localStorage` gespeichert.

**Neue Sprache hinzufügen:**
1. `ui/i18n/{lang}.json` erstellen (von `en.json` kopieren)
2. Zur Sprachliste in `js/i18n.js` hinzufügen
3. Zur Sprachauswahl in `index.html` hinzufügen
4. `app/i18n/{lang}.json` für Backend-API-Antworten erstellen

### GitHub Pages Deployment

```bash
cp -r ui/ docs/
git add docs/ && git commit -m "UI deployen" && git push
# Dann: Settings → Pages → Branch: main, Ordner: /docs
```

</details>

---

<a id="français"></a>

<details>
<summary>🇫🇷 Français — Cliquer pour développer</summary>

## Français

### Vue d'ensemble

L'interface est un tableau de bord web côté client sous `/ui`. Il communique avec le backend FastAPI via API REST. Aucune étape de construction requise — HTML pur + JavaScript vanilla + CSS.

### Structure des fichiers

```
ui/
├── index.html         # Page principale du tableau de bord
├── js/
│   ├── app.js         # Logique applicative (toutes les interactions UI)
│   ├── api.js         # Module de requêtes API (wrapper fetch)
│   ├── i18n.js        # Moteur multilingue
│   └── components.js  # Composants UI réutilisables
├── css/
│   ├── theme.css      # Système de couleurs, variables CSS
│   ├── layout.css     # Grille et mise en page
│   └── components.css # Styles boutons, formulaires, cartes
└── i18n/
    ├── tr.json / en.json / de.json / fr.json
```

### Sections du tableau de bord

| Section | Description |
|---------|-------------|
| 🔌 Connexion | Connecter l'imprimante USB/LAN, indicateur d'état |
| 🖨️ Imprimer texte | Texte multi-lignes formaté |
| 📷 Imprimer QR | Générateur de QR code |
| ♻️ ACO Recycling | Formulaire de reçu de récompense avec aperçu |
| 📊 Journaux | Historique d'impression avec filtre et export CSV |
| 🗞️ Rouleau papier | Suivi du rouleau, mètres restants |
| ⚙️ Paramètres | URL API, token, sélection de langue |

### Système i18n

Toutes les 94 étiquettes UI sont pilotées par des attributs `data-i18n`. Lors du changement de langue, `i18n.applyTranslations()` met à jour tous les éléments. La langue sélectionnée est persistée dans `localStorage`.

**Ajouter une nouvelle langue:**
1. Créer `ui/i18n/{lang}.json` (copier depuis `en.json`)
2. Ajouter à la liste des langues dans `js/i18n.js`
3. Ajouter au sélecteur de langue dans `index.html`
4. Créer `app/i18n/{lang}.json` pour les réponses API backend

### Déploiement GitHub Pages

```bash
cp -r ui/ docs/
git add docs/ && git commit -m "Déployer l'UI" && git push
# Puis: Settings → Pages → Branche: main, Dossier: /docs
```

</details>

---

← [Geri / Back to root README](../README.md)
