/**
 * i18n (Internationalization) Yönetimi
 * Çoklu dil desteği
 */

class I18n {
  constructor() {
    this.currentLang = 'tr'; // Varsayılan dil
    this.translations = {};
    this.fallbackLang = 'en';
  }

  /**
   * Dil dosyasını yükle
   */
  async loadLanguage(lang) {
    try {
      const response = await fetch(`/ui/i18n/${lang}.json`);
      if (!response.ok) throw new Error(`Failed to load ${lang}`);
      this.translations[lang] = await response.json();
      return true;
    } catch (error) {
      console.error(`Error loading language ${lang}:`, error);
      return false;
    }
  }

  /**
   * Tüm dilleri yükle
   */
  async init() {
    const languages = ['tr', 'en', 'de', 'fr'];
    await Promise.all(languages.map(lang => this.loadLanguage(lang)));
    
    // LocalStorage'dan dil tercihini oku (öncelikli)
    const savedLang = localStorage.getItem('printer-ui-lang');
    if (savedLang && languages.includes(savedLang)) {
      this.currentLang = savedLang;
    } else {
      // Tarayıcı dilini kontrol et
      const browserLang = navigator.language.split('-')[0];
      if (languages.includes(browserLang)) {
        this.currentLang = browserLang;
      } else {
        // Varsayılan Türkçe
        this.currentLang = 'tr';
      }
    }
    
    // İlk yükleme sonrası UI'ı güncelle
    this.updateUI();
  }

  /**
   * Dili değiştir
   */
  setLanguage(lang) {
    if (!this.translations[lang]) {
      console.warn(`Language ${lang} not loaded`);
      return false;
    }
    this.currentLang = lang;
    localStorage.setItem('printer-ui-lang', lang);
    this.updateUI();
    return true;
  }

  /**
   * Çeviri al (nested key desteği: "app.title")
   */
  t(key, fallback = key) {
    const keys = key.split('.');
    let value = this.translations[this.currentLang];
    
    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k];
      } else {
        // Fallback dilde dene
        value = this.translations[this.fallbackLang];
        for (const fk of keys) {
          if (value && typeof value === 'object' && fk in value) {
            value = value[fk];
          } else {
            return fallback;
          }
        }
        break;
      }
    }
    
    return typeof value === 'string' ? value : fallback;
  }

  /**
   * UI'daki tüm metinleri güncelle
   */
  updateUI() {
    // data-i18n attribute'u olan tüm elementleri güncelle
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      const text = this.t(key);
      
      // Placeholder mı yoksa text mi?
      if (el.hasAttribute('placeholder')) {
        el.placeholder = text;
      } else if (el.tagName === 'INPUT' && el.type !== 'text') {
        // Checkbox, radio vb. için label güncelle
        const label = el.closest('label');
        if (label) {
          const labelText = label.childNodes[label.childNodes.length - 1];
          if (labelText.nodeType === Node.TEXT_NODE) {
            labelText.textContent = text;
          }
        }
      } else {
        el.textContent = text;
      }
    });

    // data-i18n-title attribute'u olan elementleri güncelle (tooltip)
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
      const key = el.getAttribute('data-i18n-title');
      el.title = this.t(key);
    });

    // Select option'ları güncelle
    document.querySelectorAll('option[data-i18n]').forEach(option => {
      const key = option.getAttribute('data-i18n');
      option.textContent = this.t(key);
    });

    // Dil butonlarını güncelle
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.lang === this.currentLang);
    });

    // Custom event dispatch et
    document.dispatchEvent(new CustomEvent('languageChanged', {
      detail: { lang: this.currentLang }
    }));
  }

  /**
   * Mevcut dili al
   */
  getCurrentLanguage() {
    return this.currentLang;
  }

  /**
   * Tüm mevcut dilleri al
   */
  getAvailableLanguages() {
    return Object.keys(this.translations);
  }
}

// Global instance
const i18n = new I18n();

// Export
window.i18n = i18n;
