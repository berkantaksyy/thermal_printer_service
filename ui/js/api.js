/**
 * API İletişim Modülü
 * Tüm backend API çağrıları
 */

class API {
  constructor() {
    this.baseURL = localStorage.getItem('printer-api-url') || 'http://localhost:8000';
    this.token = localStorage.getItem('printer-api-token') || 'change-me-secret-token';
  }

  /**
   * API URL'ini ayarla
   */
  setBaseURL(url) {
    this.baseURL = url.replace(/\/$/, ''); // Trailing slash kaldır
    localStorage.setItem('printer-api-url', this.baseURL);
  }

  /**
   * API token'ı ayarla
   */
  setToken(token) {
    this.token = token;
    localStorage.setItem('printer-api-token', token);
  }

  /**
   * HTTP isteği gönder
   */
  async request(method, endpoint, body = null) {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
    };

    // /health endpoint'i hariç token ekle
    if (!endpoint.includes('/health')) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const options = {
      method,
      headers,
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(url, options);
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new APIError(
          data?.detail?.error?.code || data?.detail || 'UNKNOWN_ERROR',
          data?.detail?.error?.detail || data?.message || 'An error occurred',
          response.status,
          data
        );
      }

      return data;
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      // Network hatası
      throw new APIError(
        'NETWORK_ERROR',
        'Sunucuya bağlanılamadı. Lütfen bağlantınızı kontrol edin.',
        0,
        { originalError: error.message }
      );
    }
  }

  /**
   * GET kısayol metodu
   */
  async get(endpoint) {
    return this.request('GET', endpoint);
  }

  /**
   * POST kısayol metodu
   */
  async post(endpoint, body = null) {
    return this.request('POST', endpoint, body);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // HEALTH & STATUS
  // ═══════════════════════════════════════════════════════════════════════════

  async getHealth() {
    return this.request('GET', '/health');
  }

  async getStatus() {
    return this.request('GET', '/status');
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // CONNECTION
  // ═══════════════════════════════════════════════════════════════════════════

  async connect(connectionType, options = {}) {
    const body = { connection_type: connectionType, ...options };
    return this.request('POST', '/connect', body);
  }

  async disconnect() {
    return this.request('POST', '/connect/disconnect');
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // PRINT
  // ═══════════════════════════════════════════════════════════════════════════

  async printText(data) {
    return this.request('POST', '/print/text', data);
  }

  async printQR(data) {
    return this.request('POST', '/print/qr', data);
  }

  async printImage(data) {
    return this.request('POST', '/print/image', data);
  }

  async printSmart(data) {
    return this.request('POST', '/print/smart', data);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // LOGS
  // ═══════════════════════════════════════════════════════════════════════════

  async getLogs(params = {}) {
    const query = new URLSearchParams(params).toString();
    return this.request('GET', `/logs${query ? '?' + query : ''}`);
  }

  async exportLogs() {
    const url = `${this.baseURL}/logs/export`;
    const response = await fetch(url, {
      headers: { 'Authorization': `Bearer ${this.token}` }
    });
    
    if (!response.ok) {
      throw new Error('Failed to export logs');
    }
    
    const blob = await response.blob();
    return blob;
  }

  async getFailedJobs() {
    return this.request('GET', '/logs/failed');
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // REPRINT
  // ═══════════════════════════════════════════════════════════════════════════

  async reprint(jobId) {
    return this.request('POST', '/reprint', { job_id: jobId });
  }
}

/**
 * API Hata Sınıfı
 */
class APIError extends Error {
  constructor(code, message, status, data) {
    super(message);
    this.name = 'APIError';
    this.code = code;
    this.status = status;
    this.data = data;
  }

  /**
   * Kullanıcı dostu hata mesajı
   */
  getUserMessage() {
    const errorMessages = {
      'PAPER_OUT': '📄 Kağıt bitti. Lütfen kağıt yükleyin.',
      'PAPER_JAM': '📄 Kağıt sıkıştı. Lütfen kontrol edin.',
      'COVER_OPEN': '🔓 Yazıcı kapağı açık. Lütfen kapatın.',
      'OVERHEAT': '🌡️ Yazıcı aşırı ısındı. Lütfen soğumasını bekleyin.',
      'COMM_ERROR': '🔌 Yazıcı ile iletişim kurulamadı.',
      'NOT_CONNECTED': '🔌 Yazıcı bağlı değil. Lütfen önce bağlantı kurun.',
      'NETWORK_ERROR': '🌐 Sunucuya bağlanılamadı. Bağlantınızı kontrol edin.',
      'UNAUTHORIZED': '🔐 Geçersiz API token. Lütfen token\'ı kontrol edin.',
      'UNKNOWN_ERROR': '❌ Bilinmeyen bir hata oluştu.',
    };

    return errorMessages[this.code] || this.message;
  }
}

// Global instance
const api = new API();

// Export
window.api = api;
window.APIError = APIError;
