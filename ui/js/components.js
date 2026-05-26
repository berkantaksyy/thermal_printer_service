/**
 * UI Bileşenleri
 * Toast, Loading, Modal vb.
 */

class UIComponents {
  constructor() {
    this.toastContainer = null;
    this.init();
  }

  init() {
    // Toast container oluştur
    this.toastContainer = document.createElement('div');
    this.toastContainer.className = 'toast-container';
    document.body.appendChild(this.toastContainer);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // TOAST NOTIFICATIONS
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Toast göster
   */
  toast(message, type = 'info', duration = 4000) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️'
    };

    toast.innerHTML = `
      <div class="toast-icon">${icons[type] || icons.info}</div>
      <div class="toast-content">
        <div class="toast-message">${this.escapeHtml(message)}</div>
      </div>
    `;

    this.toastContainer.appendChild(toast);

    // Animasyon sonrası kaldır
    setTimeout(() => {
      toast.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, duration);

    return toast;
  }

  success(message, duration) {
    return this.toast(message, 'success', duration);
  }

  error(message, duration) {
    return this.toast(message, 'error', duration);
  }

  warning(message, duration) {
    return this.toast(message, 'warning', duration);
  }

  info(message, duration) {
    return this.toast(message, 'info', duration);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // LOADING STATE
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Butona loading state ekle
   */
  setButtonLoading(button, loading = true) {
    if (loading) {
      button.disabled = true;
      button.classList.add('loading');
      button.dataset.originalText = button.textContent;
    } else {
      button.disabled = false;
      button.classList.remove('loading');
      if (button.dataset.originalText) {
        button.textContent = button.dataset.originalText;
      }
    }
  }

  /**
   * Form'u disable/enable et
   */
  setFormLoading(form, loading = true) {
    const inputs = form.querySelectorAll('input, select, textarea, button');
    inputs.forEach(input => {
      input.disabled = loading;
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // FORM VALIDATION
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Form hatasını göster
   */
  showFieldError(field, message) {
    // Mevcut hatayı temizle
    this.clearFieldError(field);

    // Hata mesajı ekle
    const error = document.createElement('div');
    error.className = 'form-error';
    error.textContent = message;
    field.parentNode.appendChild(error);

    // Input'a hata stili
    field.style.borderColor = 'var(--error)';
  }

  /**
   * Form hatasını temizle
   */
  clearFieldError(field) {
    const error = field.parentNode.querySelector('.form-error');
    if (error) error.remove();
    field.style.borderColor = '';
  }

  /**
   * Tüm form hatalarını temizle
   */
  clearFormErrors(form) {
    form.querySelectorAll('.form-error').forEach(error => error.remove());
    form.querySelectorAll('input, select, textarea').forEach(field => {
      field.style.borderColor = '';
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // DRAG & DROP
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Drag & drop zone oluştur
   */
  setupDropzone(element, onFileDrop) {
    element.addEventListener('dragover', (e) => {
      e.preventDefault();
      element.classList.add('dragover');
    });

    element.addEventListener('dragleave', () => {
      element.classList.remove('dragover');
    });

    element.addEventListener('drop', (e) => {
      e.preventDefault();
      element.classList.remove('dragover');
      
      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        onFileDrop(files[0]);
      }
    });

    // Click to select
    element.addEventListener('click', () => {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = element.dataset.accept || '*';
      input.onchange = (e) => {
        if (e.target.files.length > 0) {
          onFileDrop(e.target.files[0]);
        }
      };
      input.click();
    });
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // FILE HANDLING
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Dosyayı base64'e çevir
   */
  fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        // Data URL'den base64 kısmını al
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  /**
   * Dosya boyutunu formatla
   */
  formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // UTILITIES
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * HTML escape
   */
  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  /**
   * Debounce fonksiyonu
   */
  debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  /**
   * Element'i göster/gizle
   */
  toggle(element, show) {
    if (show === undefined) {
      element.classList.toggle('hidden');
    } else {
      element.classList.toggle('hidden', !show);
    }
  }

  /**
   * Scroll to element
   */
  scrollTo(element, behavior = 'smooth') {
    element.scrollIntoView({ behavior, block: 'start' });
  }

  /**
   * Copy to clipboard
   */
  async copyToClipboard(text) {
    try {
      await navigator.clipboard.writeText(text);
      this.success('Panoya kopyalandı');
      return true;
    } catch (error) {
      this.error('Kopyalama başarısız');
      return false;
    }
  }

  /**
   * Download file
   */
  downloadFile(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  /**
   * Format date
   */
  formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (seconds < 60) return 'Az önce';
    if (minutes < 60) return `${minutes} dakika önce`;
    if (hours < 24) return `${hours} saat önce`;
    if (days < 7) return `${days} gün önce`;

    return date.toLocaleDateString('tr-TR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  /**
   * Format duration (seconds)
   */
  formatDuration(seconds) {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}dk`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}sa`;
    return `${Math.floor(seconds / 86400)}g`;
  }

  /**
   * Validate JSON
   */
  isValidJSON(str) {
    try {
      JSON.parse(str);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Format JSON
   */
  formatJSON(obj) {
    return JSON.stringify(obj, null, 2);
  }
}

// Slideout animasyonu ekle
const style = document.createElement('style');
style.textContent = `
  @keyframes slideOut {
    to {
      opacity: 0;
      transform: translateX(100%);
    }
  }
`;
document.head.appendChild(style);

// Global instance
const ui = new UIComponents();

// Export
window.ui = ui;
