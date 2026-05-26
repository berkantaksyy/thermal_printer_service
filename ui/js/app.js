/**
 * Ana Uygulama Mantığı
 * Termal Yazıcı Servisi UI
 */

class PrinterApp {
  constructor() {
    this.statusInterval = null;
    this.init();
  }

  /**
   * Uygulamayı başlat
   */
  async init() {
    // i18n yükle (updateUI otomatik çağrılıyor)
    await i18n.init();

    // Event listener'ları ekle
    this.setupEventListeners();

    // İlk durum kontrolü
    await this.refreshStatus();

    // Otomatik durum yenileme (15 saniye)
    this.statusInterval = setInterval(() => this.refreshStatus(), 15000);

    // Logları yükle
    await this.loadLogs();

    console.log('✅ Printer App initialized');
  }

  /**
   * Event listener'ları kur
   */
  setupEventListeners() {
    // Dil değiştirme
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        i18n.setLanguage(btn.dataset.lang);
      });
    });

    // API ayarları
    const apiUrlInput = document.getElementById('apiUrl');
    const apiTokenInput = document.getElementById('apiToken');
    
    if (apiUrlInput) {
      apiUrlInput.value = api.baseURL;
      apiUrlInput.addEventListener('change', (e) => {
        api.setBaseURL(e.target.value);
      });
    }
    
    if (apiTokenInput) {
      apiTokenInput.value = api.token;
      apiTokenInput.addEventListener('change', (e) => {
        api.setToken(e.target.value);
      });
    }

    // Bağlantı tipi değişimi
    const connTypeSelect = document.getElementById('connType');
    if (connTypeSelect) {
      connTypeSelect.addEventListener('change', () => this.toggleConnectionFields());
      this.toggleConnectionFields();
    }

    // Bağlantı butonları
    const connectBtn = document.getElementById('connectBtn');
    const disconnectBtn = document.getElementById('disconnectBtn');
    
    if (connectBtn) {
      connectBtn.addEventListener('click', () => this.handleConnect());
    }
    
    if (disconnectBtn) {
      disconnectBtn.addEventListener('click', () => this.handleDisconnect());
    }

    // Yazdırma butonları
    const printTextBtn = document.getElementById('printTextBtn');
    const printQRBtn = document.getElementById('printQRBtn');
    const printImageBtn = document.getElementById('printImageBtn');
    const printSmartBtn = document.getElementById('printSmartBtn');
    
    if (printTextBtn) {
      printTextBtn.addEventListener('click', () => this.handlePrintText());
    }
    
    if (printQRBtn) {
      printQRBtn.addEventListener('click', () => this.handlePrintQR());
    }
    
    if (printImageBtn) {
      printImageBtn.addEventListener('click', () => this.handlePrintImage());
    }
    
    if (printSmartBtn) {
      printSmartBtn.addEventListener('click', () => this.handlePrintSmart());
    }

    // Log butonları
    const refreshLogsBtn = document.getElementById('refreshLogsBtn');
    const exportLogsBtn = document.getElementById('exportLogsBtn');
    
    if (refreshLogsBtn) {
      refreshLogsBtn.addEventListener('click', () => this.loadLogs());
    }
    
    if (exportLogsBtn) {
      exportLogsBtn.addEventListener('click', () => this.exportLogs());
    }

    // Durum yenileme butonu
    const refreshStatusBtn = document.getElementById('refreshStatusBtn');
    if (refreshStatusBtn) {
      refreshStatusBtn.addEventListener('click', () => this.refreshStatus());
    }

    // Image dropzone
    const imageDropzone = document.getElementById('imageDropzone');
    if (imageDropzone) {
      ui.setupDropzone(imageDropzone, (file) => this.handleImageFile(file));
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // STATUS & HEALTH
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Durum bilgisini yenile
   */
  async refreshStatus() {
    try {
      const health = await api.getHealth();
      
      // Durum dot'unu güncelle
      const statusDot = document.getElementById('statusDot');
      const statusText = document.getElementById('statusText');
      
      if (statusDot && statusText) {
        if (health.printer_connected) {
          statusDot.className = 'status-dot success';
          statusText.textContent = i18n.t('status.connected');
        } else {
          statusDot.className = 'status-dot inactive';
          statusText.textContent = i18n.t('status.disconnected');
        }
      }

      // Kuyruk boyutu
      const queueSize = document.getElementById('queueSize');
      if (queueSize) {
        queueSize.textContent = health.queue_size || 0;
      }

      // Çalışma süresi
      const uptime = document.getElementById('uptime');
      if (uptime) {
        uptime.textContent = ui.formatDuration(health.uptime_seconds || 0);
      }

      // Bellek
      const memory = document.getElementById('memory');
      if (memory) {
        memory.textContent = `${health.memory_mb || 0} MB`;
      }

    } catch (error) {
      console.error('Status refresh error:', error);
      // Hata durumunda dot'u kırmızı yap
      const statusDot = document.getElementById('statusDot');
      if (statusDot) {
        statusDot.className = 'status-dot error';
      }
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // CONNECTION
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Bağlantı alanlarını göster/gizle
   */
  toggleConnectionFields() {
    const connType = document.getElementById('connType')?.value;
    const usbFields = document.getElementById('usbFields');
    const lanFields = document.getElementById('lanFields');
    
    if (usbFields && lanFields) {
      usbFields.classList.toggle('hidden', connType !== 'usb');
      lanFields.classList.toggle('hidden', connType !== 'lan');
    }
  }

  /**
   * Bağlan
   */
  async handleConnect() {
    const btn = document.getElementById('connectBtn');
    const connType = document.getElementById('connType')?.value;
    
    if (!connType) return;

    try {
      ui.setButtonLoading(btn, true);

      const options = {};
      
      if (connType === 'usb') {
        const vendor = document.getElementById('usbVendor')?.value;
        const product = document.getElementById('usbProduct')?.value;
        if (vendor) options.usb_vendor_id = parseInt(vendor, 16);
        if (product) options.usb_product_id = parseInt(product, 16);
      } else {
        const host = document.getElementById('lanHost')?.value;
        const port = document.getElementById('lanPort')?.value;
        if (host) options.lan_host = host;
        if (port) options.lan_port = parseInt(port);
      }

      const result = await api.connect(connType, options);
      ui.success(result.message || 'Bağlantı başarılı');
      await this.refreshStatus();

    } catch (error) {
      ui.error(error instanceof APIError ? error.getUserMessage() : error.message);
    } finally {
      ui.setButtonLoading(btn, false);
    }
  }

  /**
   * Bağlantıyı kes
   */
  async handleDisconnect() {
    const btn = document.getElementById('disconnectBtn');
    
    try {
      ui.setButtonLoading(btn, true);
      const result = await api.disconnect();
      ui.success(result.message || 'Bağlantı kesildi');
      await this.refreshStatus();

    } catch (error) {
      ui.error(error instanceof APIError ? error.getUserMessage() : error.message);
    } finally {
      ui.setButtonLoading(btn, false);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // PRINT - TEXT
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Metin yazdır
   */
  async handlePrintText() {
    const btn = document.getElementById('printTextBtn');
    const jobId = document.getElementById('textJobId')?.value || undefined;
    const content = document.getElementById('textContent')?.value;
    const bold = document.getElementById('textBold')?.checked || false;
    const underline = document.getElementById('textUnderline')?.checked || false;
    const align = document.getElementById('textAlign')?.value || 'left';
    const fontSize = document.getElementById('textFontSize')?.value || 'normal';
    const autoCut = document.getElementById('textAutoCut')?.checked !== false;

    if (!content || content.trim() === '') {
      ui.warning('Lütfen yazdırılacak metni girin');
      return;
    }

    try {
      ui.setButtonLoading(btn, true);

      // Her satırı ayrı line objesi yap
      const lines = content.split('\n').map(text => ({
        text,
        bold,
        underline,
        align,
        font_size: fontSize
      }));

      const data = {
        lines,
        cut: autoCut,
        language: i18n.getCurrentLanguage()
      };

      if (jobId) data.job_id = jobId;

      const result = await api.printText(data);
      ui.success(`✅ ${result.message} (${result.job_id})`);
      
      // Formu temizle
      document.getElementById('textContent').value = '';
      
      // Logları yenile
      setTimeout(() => this.loadLogs(), 1000);

    } catch (error) {
      ui.error(error instanceof APIError ? error.getUserMessage() : error.message);
    } finally {
      ui.setButtonLoading(btn, false);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // PRINT - QR CODE
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * QR kod yazdır
   */
  async handlePrintQR() {
    const btn = document.getElementById('printQRBtn');
    const jobId = document.getElementById('qrJobId')?.value || undefined;
    const qrData = document.getElementById('qrData')?.value;
    const label = document.getElementById('qrLabel')?.value || undefined;
    const size = parseInt(document.getElementById('qrSize')?.value || '6');
    const errorCorrection = document.getElementById('qrErrorCorrection')?.value || 'M';
    const align = document.getElementById('qrAlign')?.value || 'center';
    const autoCut = document.getElementById('qrAutoCut')?.checked !== false;

    if (!qrData || qrData.trim() === '') {
      ui.warning('Lütfen QR içeriğini girin');
      return;
    }

    try {
      ui.setButtonLoading(btn, true);

      const data = {
        data: qrData,
        size,
        error_correction: errorCorrection,
        align,
        cut: autoCut,
        language: i18n.getCurrentLanguage()
      };

      if (jobId) data.job_id = jobId;
      if (label) data.label = label;

      const result = await api.printQR(data);
      ui.success(`✅ ${result.message} (${result.job_id})`);
      
      // Formu temizle
      document.getElementById('qrData').value = '';
      if (document.getElementById('qrLabel')) {
        document.getElementById('qrLabel').value = '';
      }
      
      setTimeout(() => this.loadLogs(), 1000);

    } catch (error) {
      ui.error(error instanceof APIError ? error.getUserMessage() : error.message);
    } finally {
      ui.setButtonLoading(btn, false);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // PRINT - IMAGE
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Görsel dosyasını işle
   */
  async handleImageFile(file) {
    const preview = document.getElementById('imagePreview');
    const fileName = document.getElementById('imageFileName');
    
    if (preview) {
      const reader = new FileReader();
      reader.onload = (e) => {
        preview.src = e.target.result;
        preview.classList.remove('hidden');
      };
      reader.readAsDataURL(file);
    }
    
    if (fileName) {
      fileName.textContent = `${file.name} (${ui.formatFileSize(file.size)})`;
    }
    
    // Dosyayı sakla
    this.selectedImageFile = file;
  }

  /**
   * Görsel yazdır
   */
  async handlePrintImage() {
    const btn = document.getElementById('printImageBtn');
    const jobId = document.getElementById('imageJobId')?.value || undefined;
    const align = document.getElementById('imageAlign')?.value || 'center';
    const autoCut = document.getElementById('imageAutoCut')?.checked !== false;

    if (!this.selectedImageFile) {
      ui.warning('Lütfen bir görsel seçin');
      return;
    }

    try {
      ui.setButtonLoading(btn, true);

      // Dosyayı base64'e çevir
      const base64 = await ui.fileToBase64(this.selectedImageFile);

      const data = {
        image_base64: base64,
        align,
        cut: autoCut,
        language: i18n.getCurrentLanguage()
      };

      if (jobId) data.job_id = jobId;

      const result = await api.printImage(data);
      ui.success(`✅ ${result.message} (${result.job_id})`);
      
      // Önizlemeyi temizle
      const preview = document.getElementById('imagePreview');
      if (preview) {
        preview.src = '';
        preview.classList.add('hidden');
      }
      
      const fileName = document.getElementById('imageFileName');
      if (fileName) {
        fileName.textContent = '';
      }
      
      this.selectedImageFile = null;
      
      setTimeout(() => this.loadLogs(), 1000);

    } catch (error) {
      ui.error(error instanceof APIError ? error.getUserMessage() : error.message);
    } finally {
      ui.setButtonLoading(btn, false);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // PRINT - SMART (AI)
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Akıllı yazdırma (AI)
   */
  async handlePrintSmart() {
    const btn = document.getElementById('printSmartBtn');
    const jobId = document.getElementById('smartJobId')?.value || undefined;
    const hint = document.getElementById('smartHint')?.value || undefined;
    const jsonData = document.getElementById('smartData')?.value;
    const language = document.getElementById('smartLang')?.value || i18n.getCurrentLanguage();
    const autoCut = document.getElementById('smartAutoCut')?.checked !== false;

    if (!jsonData || jsonData.trim() === '') {
      ui.warning('Lütfen JSON veri girin');
      return;
    }

    // JSON validasyonu
    if (!ui.isValidJSON(jsonData)) {
      ui.error('Geçersiz JSON formatı');
      return;
    }

    try {
      ui.setButtonLoading(btn, true);

      const data = {
        data: JSON.parse(jsonData),
        cut: autoCut,
        language
      };

      if (jobId) data.job_id = jobId;
      if (hint) data.template_hint = hint;

      const result = await api.printSmart(data);
      ui.success(`🤖 ${result.message} (${result.job_id})`);
      
      setTimeout(() => this.loadLogs(), 1000);

    } catch (error) {
      ui.error(error instanceof APIError ? error.getUserMessage() : error.message);
    } finally {
      ui.setButtonLoading(btn, false);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // LOGS
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Logları yükle
   */
  async loadLogs() {
    try {
      const result = await api.getLogs({ page: 1, page_size: 50 });
      this.renderLogs(result.entries || []);
    } catch (error) {
      console.error('Failed to load logs:', error);
    }
  }

  /**
   * Logları render et
   */
  renderLogs(entries) {
    const tbody = document.getElementById('logsTableBody');
    if (!tbody) return;

    if (entries.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" class="table-empty" data-i18n="logs.empty">
            ${i18n.t('logs.empty')}
          </td>
        </tr>
      `;
      return;
    }

    // En yeni loglar üstte
    const sortedEntries = [...entries].reverse();

    tbody.innerHTML = sortedEntries.map(entry => {
      const statusClass = entry.status === 'done' ? 'success' :
                         entry.status === 'failed' ? 'error' : 'secondary';
      
      const time = entry.ts ? new Date(entry.ts).toLocaleString('tr-TR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }) : '—';

      const jobIdShort = entry.job_id ? entry.job_id.substring(0, 12) + '...' : '—';
      const errorText = entry.error ?
        `${entry.error.code || ''} ${entry.error.detail || ''}`.trim() : '';

      return `
        <tr>
          <td class="font-mono text-secondary">${time}</td>
          <td>${entry.op || '—'}</td>
          <td class="font-mono" style="font-size: 11px;">${jobIdShort}</td>
          <td><span class="badge badge-${statusClass}">${entry.status}</span></td>
          <td class="text-error" style="font-size: 11px;">${errorText}</td>
        </tr>
      `;
    }).join('');
  }

  /**
   * Logları CSV olarak indir
   */
  async exportLogs() {
    const btn = document.getElementById('exportLogsBtn');
    
    try {
      ui.setButtonLoading(btn, true);
      const blob = await api.exportLogs();
      ui.downloadFile(blob, 'printer_logs.csv');
      ui.success('CSV dosyası indirildi');
    } catch (error) {
      ui.error('CSV indirme başarısız');
    } finally {
      ui.setButtonLoading(btn, false);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // CLEANUP
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Temizlik
   */
  destroy() {
    if (this.statusInterval) {
      clearInterval(this.statusInterval);
    }
  }
}

// Sayfa yüklendiğinde uygulamayı başlat
let app;
document.addEventListener('DOMContentLoaded', () => {
  app = new PrinterApp();
});

// Sayfa kapatılırken temizlik
window.addEventListener('beforeunload', () => {
  if (app) {
    app.destroy();
  }
});

// Export
window.app = app;
