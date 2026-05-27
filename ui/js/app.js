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

    // Rulo durumunu yükle
    await this.loadPaperStats();

    // Log otomatik yenileme başlat (30 saniye)
    this.startLogAutoRefresh();

    console.log('✅ Printer App initialized');
  }

  /**
   * Event listener'ları kur
   */
  setupEventListeners() {
    // Dil değiştirme (UI dili)
    document.querySelectorAll('.lang-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        i18n.setLanguage(btn.dataset.lang);
        // UI dili değişince yazıcı dili de otomatik senkronize et (kullanıcı elle değiştirmediyse)
        const printerLangEl = document.getElementById('printerLang');
        if (printerLangEl && !printerLangEl.dataset.manuallySet) {
          printerLangEl.value = btn.dataset.lang;
        }
      });
    });

    // Yazıcı mesaj dili değiştirilirse manuel olarak ayarlandığını işaretle
    const printerLangEl = document.getElementById('printerLang');
    if (printerLangEl) {
      printerLangEl.addEventListener('change', () => {
        printerLangEl.dataset.manuallySet = 'true';
      });
    }

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

    // ACO Recycling
    const printAcoBtn = document.getElementById('printAcoBtn');
    if (printAcoBtn) {
      printAcoBtn.addEventListener('click', () => this.handlePrintAco());
    }

    // Log butonları
    const refreshLogsBtn = document.getElementById('refreshLogsBtn');
    const exportLogsBtn = document.getElementById('exportLogsBtn');
    const logFilterSelect = document.getElementById('logFilterSelect');

    if (refreshLogsBtn) {
      refreshLogsBtn.addEventListener('click', () => {
        const filter = logFilterSelect?.value;
        this.loadLogs(filter === 'all' ? null : filter);
      });
    }

    if (exportLogsBtn) {
      exportLogsBtn.addEventListener('click', () => this.exportLogs());
    }

    if (logFilterSelect) {
      logFilterSelect.addEventListener('change', () => {
        const filter = logFilterSelect.value;
        this.loadLogs(filter === 'all' ? null : filter);
      });
    }

    // Durum yenileme butonu
    const refreshStatusBtn = document.getElementById('refreshStatusBtn');
    if (refreshStatusBtn) {
      refreshStatusBtn.addEventListener('click', () => this.refreshStatus());
    }

    // Rulo sıfırlama butonları
    ['paperResetBtn', 'paperResetBtnBanner'].forEach(id => {
      const btn = document.getElementById(id);
      if (btn) btn.addEventListener('click', () => this.resetPaperRoll());
    });

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

      // Kağıt durumu (health'den gelen hızlı veri)
      const pct = health.paper_remaining_pct ?? 100;
      this._updatePaperBar(pct);

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
  // PAPER ROLL
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Rulo durumunu API'den çek ve UI'ı güncelle
   */
  async loadPaperStats() {
    try {
      const stats = await api.request('GET', '/paper');
      this._renderPaperStats(stats);
    } catch (e) {
      console.warn('Paper stats unavailable:', e);
    }
  }

  _updatePaperBar(pct) {
    const fill = document.getElementById('paperBarFill');
    const label = document.getElementById('paperPct');
    if (!fill || !label) return;

    const color = pct > 50 ? '#22c55e' : pct > 20 ? '#f59e0b' : '#ef4444';
    fill.style.width = `${Math.max(0, Math.min(100, pct))}%`;
    fill.style.background = color;
    label.textContent = `${pct.toFixed(0)}%`;
    label.style.color = color;

    // Uyarı bandı
    const banner = document.getElementById('paperWarningBanner');
    const warningText = document.getElementById('paperWarningText');
    if (banner && warningText) {
      if (pct <= 10) {
        banner.classList.remove('hidden');
        banner.style.display = 'flex';
        warningText.textContent = `⚠️ ${i18n.t('paper.critical_warning')} (%${pct.toFixed(0)} ${i18n.t('paper.remaining_pct')})`;
      } else if (pct <= 20) {
        banner.classList.remove('hidden');
        banner.style.display = 'flex';
        warningText.textContent = `⚠️ ${i18n.t('paper.low_warning')} (%${pct.toFixed(0)} ${i18n.t('paper.remaining_pct')})`;
      } else {
        banner.style.display = 'none';
      }
    }
  }

  _renderPaperStats(stats) {
    if (!stats) return;
    const pct = stats.remaining_pct ?? 100;

    // Progress bar (main)
    const mainBar = document.getElementById('paperProgressBar');
    const color = pct > 50 ? '#22c55e' : pct > 20 ? '#f59e0b' : '#ef4444';
    if (mainBar) {
      mainBar.style.width = `${Math.max(0, pct)}%`;
      mainBar.style.background = color;
    }

    // Labels (i18n-aware)
    const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
    set('paperRemainingLabel', `${pct.toFixed(1)}% — ${stats.remaining_m} ${i18n.t('paper.remaining_m')}`);
    set('paperPrintsLabel', `~${stats.prints_remaining} ${i18n.t('paper.prints_remaining')}`);
    set('paperTotal', `${(stats.total_roll_mm / 1000).toFixed(0)} m`);
    set('paperUsed', `${(stats.used_mm / 1000).toFixed(2)} m`);
    set('paperPrintCount', `${stats.print_count} ${i18n.t('paper.print_count_unit')}`);
    set('paperAvg', `${stats.avg_mm_per_print} mm`);

    this._updatePaperBar(pct);
  }

  async resetPaperRoll() {
    const btn = document.getElementById('paperResetBtn');
    try {
      if (btn) ui.setButtonLoading(btn, true);
      await api.request('POST', `/paper/reset?language=${this.getPrinterLanguage()}`);
      ui.success(`🗞️ ${i18n.t('paper.reset_done')}`);
      await this.loadPaperStats();
    } catch (e) {
      ui.error(i18n.t('paper.reset_error'));
    } finally {
      if (btn) ui.setButtonLoading(btn, false);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // PRINT HELPERS
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Yazıcı mesaj dilini döndür (hata/başarı mesajları için)
   * Kullanıcının üst ayar panelindeki seçimi; yoksa UI diline düşer.
   */
  getPrinterLanguage() {
    return document.getElementById('printerLang')?.value || i18n.getCurrentLanguage();
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
        language: this.getPrinterLanguage()
      };

      if (jobId) data.job_id = jobId;

      const result = await api.printText(data);
      ui.success(`✅ ${result.message} (${result.job_id})`);

      // Önizlemeyi göster
      this.showReceiptPreview('text', { lines, jobId: result.job_id });

      // Formu temizle
      document.getElementById('textContent').value = '';

      // Logları yenile
      setTimeout(() => { this.loadLogs(); this.loadPaperStats(); }, 1000);

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
        language: this.getPrinterLanguage()
      };

      if (jobId) data.job_id = jobId;
      if (label) data.label = label;

      const result = await api.printQR(data);
      ui.success(`✅ ${result.message} (${result.job_id})`);

      // Önizlemeyi göster
      this.showReceiptPreview('qr', { qrData, label, align, size, jobId: result.job_id });

      // Formu temizle
      document.getElementById('qrData').value = '';
      if (document.getElementById('qrLabel')) {
        document.getElementById('qrLabel').value = '';
      }

      setTimeout(() => { this.loadLogs(); this.loadPaperStats(); }, 1000);

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
        language: this.getPrinterLanguage()
      };

      if (jobId) data.job_id = jobId;

      const result = await api.printImage(data);
      ui.success(`✅ ${result.message} (${result.job_id})`);

      // Baskı önizlemesini göster
      const uploadedPreviewSrc = document.getElementById('imagePreview')?.src;
      this.showReceiptPreview('image', { src: uploadedPreviewSrc, align, jobId: result.job_id });

      // Yükleme önizlemesini temizle
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
      
      setTimeout(() => { this.loadLogs(); this.loadPaperStats(); }, 1000);

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

      // Önizlemeyi göster
      this.showReceiptPreview('smart', { data: JSON.parse(jsonData), hint, jobId: result.job_id });

      setTimeout(() => { this.loadLogs(); this.loadPaperStats(); }, 1000);

    } catch (error) {
      ui.error(error instanceof APIError ? error.getUserMessage() : error.message);
    } finally {
      ui.setButtonLoading(btn, false);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // PRINT - ACO RECYCLING
  // ═══════════════════════════════════════════════════════════════════════════

  async handlePrintAco() {
    const btn = document.getElementById('printAcoBtn');
    const jobId = document.getElementById('acoJobId')?.value || undefined;
    const machineId = document.getElementById('acoMachineId')?.value;
    const reward = parseFloat(document.getElementById('acoReward')?.value || '0');
    const currency = document.getElementById('acoCurrency')?.value || 'TL';
    const glass = parseInt(document.getElementById('acoGlass')?.value || '0');
    const plastic = parseInt(document.getElementById('acoPlastic')?.value || '0');
    const metal = parseInt(document.getElementById('acoMetal')?.value || '0');
    const tetrapak = parseInt(document.getElementById('acoTetrapak')?.value || '0');
    const qrData = document.getElementById('acoQrData')?.value;
    const templateName = document.getElementById('acoTemplateName')?.value || undefined;
    const autoCut = document.getElementById('acoAutoCut')?.checked !== false;

    if (!machineId || machineId.trim() === '') {
      ui.warning('Lütfen Makine ID girin');
      return;
    }
    if (!qrData || qrData.trim() === '') {
      ui.warning('Lütfen QR kod verisini girin');
      return;
    }

    try {
      ui.setButtonLoading(btn, true);

      const data = {
        machine_id: machineId,
        reward,
        currency,
        glass,
        plastic,
        metal,
        tetrapak,
        qr_data: qrData,
        cut: autoCut,
        language: this.getPrinterLanguage(),
      };
      if (jobId) data.job_id = jobId;
      if (templateName) data.template_name = templateName;

      const result = await api.printAco(data);
      ui.success(`♻️ ${result.message} (${result.job_id})`);

      // ACO önizlemesini göster
      this.showAcoReceiptPreview({
        machineId,
        reward,
        currency,
        glass, plastic, metal, tetrapak,
        qrData,
        templateName: templateName || 'Aco Recycling Default Reward',
        jobId: result.job_id,
      });

      setTimeout(() => { this.loadLogs(); this.loadPaperStats(); }, 1000);

    } catch (error) {
      ui.error(error instanceof APIError ? error.getUserMessage() : error.message);
    } finally {
      ui.setButtonLoading(btn, false);
    }
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // RECEIPT PREVIEW
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Baskı önizlemesini göster
   * @param {'text'|'qr'|'image'|'smart'} type
   * @param {object} data
   */
  showReceiptPreview(type, data) {
    const section = document.getElementById('previewSection');
    const body = document.getElementById('receiptBody');
    const meta = document.getElementById('receiptMeta');
    if (!section || !body) return;

    // Scroll to preview
    section.style.display = '';
    body.innerHTML = '';

    const now = new Date().toLocaleString('tr-TR');

    if (type === 'text') {
      const { lines = [], jobId } = data;
      lines.forEach((line, idx) => {
        const span = document.createElement('span');
        span.className = [
          'receipt-line',
          `align-${line.align || 'left'}`,
          line.bold ? 'bold' : '',
          line.underline ? 'underline' : '',
          line.font_size === 'double' || line.font_size === 'double_height' || line.font_size === 'double_width'
            ? `font-${line.font_size}` : '',
        ].filter(Boolean).join(' ');
        span.textContent = line.text || '';
        body.appendChild(span);

        // Satır arası boşluk
        if (idx < lines.length - 1) {
          body.appendChild(document.createElement('br'));
        }
      });

      // Kesme çizgisi taklidi
      const hr = document.createElement('hr');
      hr.className = 'receipt-divider';
      body.appendChild(hr);

      // Zaman damgası
      const ts = document.createElement('div');
      ts.className = 'receipt-timestamp';
      ts.textContent = now;
      body.appendChild(ts);

      if (meta) meta.textContent = `İş ID: ${jobId || '—'}`;

    } else if (type === 'qr') {
      const { qrData, label, align = 'center', size = 6, jobId } = data;

      const header = document.createElement('div');
      header.className = 'receipt-line align-center bold';
      header.textContent = '[ QR KOD ]';
      body.appendChild(header);

      const hr1 = document.createElement('hr');
      hr1.className = 'receipt-divider';
      body.appendChild(hr1);

      // QR render area
      const qrArea = document.createElement('div');
      qrArea.className = 'receipt-qr-area';
      body.appendChild(qrArea);

      // Render QR using qrcodejs if available
      const qrSize = Math.min(Math.max(size * 14, 80), 200);
      if (window.QRCode) {
        try {
          new QRCode(qrArea, {
            text: qrData || ' ',
            width: qrSize,
            height: qrSize,
            colorDark: '#000',
            colorLight: '#fff',
            correctLevel: QRCode.CorrectLevel.M,
          });
        } catch (e) {
          qrArea.textContent = qrData;
        }
      } else {
        // Fallback: just show the text
        qrArea.style.wordBreak = 'break-all';
        qrArea.style.fontSize = '10px';
        qrArea.textContent = `[QR: ${qrData}]`;
      }

      if (label) {
        const lbl = document.createElement('div');
        lbl.className = 'receipt-qr-label';
        lbl.textContent = label;
        body.appendChild(lbl);
      }

      const hr2 = document.createElement('hr');
      hr2.className = 'receipt-divider';
      body.appendChild(hr2);

      const ts = document.createElement('div');
      ts.className = 'receipt-timestamp';
      ts.textContent = now;
      body.appendChild(ts);

      if (meta) meta.textContent = `İş ID: ${jobId || '—'}  |  Boyut: ${size}  |  Hizalama: ${align}`;

    } else if (type === 'image') {
      const { src, align = 'center', jobId } = data;

      const imgArea = document.createElement('div');
      imgArea.className = 'receipt-image-area';
      if (src) {
        const img = document.createElement('img');
        img.src = src;
        img.style.textAlign = align;
        imgArea.appendChild(img);
      } else {
        imgArea.textContent = '[Görsel]';
      }
      body.appendChild(imgArea);

      const hr = document.createElement('hr');
      hr.className = 'receipt-divider';
      body.appendChild(hr);

      const ts = document.createElement('div');
      ts.className = 'receipt-timestamp';
      ts.textContent = now;
      body.appendChild(ts);

      if (meta) meta.textContent = `İş ID: ${jobId || '—'}  |  Hizalama: ${align}`;

    } else if (type === 'smart') {
      const { data: jsonData = {}, hint, jobId } = data;

      const header = document.createElement('div');
      header.className = 'receipt-line align-center bold font-double';
      header.textContent = hint ? hint.toUpperCase() : 'AKILLI FİŞ';
      body.appendChild(header);

      const hr1 = document.createElement('hr');
      hr1.className = 'receipt-divider';
      body.appendChild(hr1);

      Object.entries(jsonData).forEach(([key, val]) => {
        const row = document.createElement('span');
        row.className = 'receipt-line align-left';
        const keyStr = key.replace(/_/g, ' ').toUpperCase();
        const valStr = String(val);
        // Pad key and value like a receipt
        const padded = keyStr.padEnd(14, ' ') + valStr;
        row.textContent = padded;
        body.appendChild(row);
        body.appendChild(document.createElement('br'));
      });

      const hr2 = document.createElement('hr');
      hr2.className = 'receipt-divider';
      body.appendChild(hr2);

      const aiNote = document.createElement('div');
      aiNote.className = 'receipt-meta';
      aiNote.textContent = '🤖 AI tarafından formatlandı';
      body.appendChild(aiNote);

      const ts = document.createElement('div');
      ts.className = 'receipt-timestamp';
      ts.textContent = now;
      body.appendChild(ts);

      if (meta) meta.textContent = `İş ID: ${jobId || '—'}`;
    }

    // Smooth scroll to preview
    setTimeout(() => {
      section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  }

  /**
   * ACO Recycling fişi önizlemesi
   */
  showAcoReceiptPreview({ machineId, reward, currency, glass, plastic, metal, tetrapak, qrData, templateName, jobId }) {
    const section = document.getElementById('previewSection');
    const body = document.getElementById('receiptBody');
    const meta = document.getElementById('receiptMeta');
    if (!section || !body) return;

    section.style.display = '';
    body.innerHTML = '';

    const CURRENCY_SYMBOLS = { TL: '₺', EUR: '€', USD: '$', GBP: '£' };
    const sym = CURRENCY_SYMBOLS[currency] || currency;
    const now = new Date().toLocaleString('tr-TR');

    // Language labels
    const lang = this.getPrinterLanguage();
    const LABELS = {
      tr: { product: 'Ürün', quantity: 'Miktar', reward: 'Puan', glass: 'Cam', plastic: 'Plastik', metal: 'Metal', tetrapak: 'Tetrapak', rewardLabel: 'ÖDÜL' },
      en: { product: 'Product', quantity: 'Qty', reward: 'Pts', glass: 'Glass', plastic: 'Plastic', metal: 'Metal', tetrapak: 'Tetrapak', rewardLabel: 'REWARD' },
      de: { product: 'Produkt', quantity: 'Menge', reward: 'Pkt', glass: 'Glas', plastic: 'Plastik', metal: 'Metall', tetrapak: 'Tetrapak', rewardLabel: 'BELOHNUNG' },
      fr: { product: 'Produit', quantity: 'Qté', reward: 'Pts', glass: 'Verre', plastic: 'Plastique', metal: 'Métal', tetrapak: 'Tetrapak', rewardLabel: 'RÉCOMPENSE' },
    };
    const L = LABELS[lang] || LABELS['en'];

    // ── Green header band ─────────────────────────────────────────────────
    const headerBand = document.createElement('div');
    headerBand.style.cssText = `
      background: linear-gradient(135deg, #1a7a1a 0%, #27ae60 100%);
      color: #fff;
      text-align: center;
      padding: 10px 8px 8px;
      border-radius: 2px 2px 0 0;
      margin: -8px -18px 0 -18px;
    `;
    headerBand.innerHTML = `
      <div style="font-size:17px; font-weight:900; letter-spacing:2px; text-shadow:0 1px 2px rgba(0,0,0,0.4);">
        ♻ ACO RECYCLING
      </div>
      <div style="font-size:9px; letter-spacing:1px; opacity:0.88; margin-top:2px; text-transform:uppercase;">
        reverse vending recycling systems
      </div>
    `;
    body.appendChild(headerBand);

    // ── Machine info ──────────────────────────────────────────────────────
    const machineDiv = document.createElement('div');
    machineDiv.style.cssText = 'text-align:center; font-size:10.5px; line-height:1.7; padding:7px 0 4px; color:#333;';
    machineDiv.innerHTML = `
      <span style="font-weight:700; color:#111;">MachineID: ${machineId}</span><br>
      <span>${now}</span><br>
      <span style="color:#666; font-size:10px;">${templateName}</span>
    `;
    body.appendChild(machineDiv);

    const hr1 = document.createElement('hr');
    hr1.className = 'receipt-divider';
    body.appendChild(hr1);

    // ── Reward amount (large, green) ──────────────────────────────────────
    const rewardBlock = document.createElement('div');
    rewardBlock.style.cssText = `
      text-align: center;
      padding: 8px 0 6px;
    `;
    rewardBlock.innerHTML = `
      <div style="font-size:10px; color:#666; letter-spacing:1px; text-transform:uppercase; margin-bottom:2px;">
        ${L.rewardLabel}
      </div>
      <div style="font-size:28px; font-weight:900; color:#1a7a1a; letter-spacing:1px; line-height:1.1;">
        ${reward.toFixed(2)} ${sym}
      </div>
    `;
    body.appendChild(rewardBlock);

    const hr2 = document.createElement('hr');
    hr2.className = 'receipt-divider';
    body.appendChild(hr2);

    // ── Product table ─────────────────────────────────────────────────────
    const table = document.createElement('table');
    table.style.cssText = 'width:100%; border-collapse:collapse; font-size:11px;';

    const thead = document.createElement('thead');
    thead.innerHTML = `
      <tr style="background:#f0f9f0; border-bottom:1px solid #27ae60;">
        <th style="text-align:left; padding:4px 3px; font-weight:700; color:#1a7a1a;">${L.product}</th>
        <th style="text-align:center; font-weight:700; color:#1a7a1a;">${L.quantity}</th>
        <th style="text-align:right; padding:4px 3px; font-weight:700; color:#1a7a1a;">${L.reward}</th>
      </tr>
    `;
    table.appendChild(thead);

    const tbody = document.createElement('tbody');
    const items = [
      { icon: '🫙', name: L.glass,    qty: glass,    pts: glass },
      { icon: '🧴', name: L.plastic,  qty: plastic,  pts: plastic },
      { icon: '🥫', name: L.metal,    qty: metal,    pts: metal },
      { icon: '🧃', name: L.tetrapak, qty: tetrapak, pts: tetrapak },
    ];
    items.forEach(({ icon, name, qty, pts }, idx) => {
      if (!qty && qty !== 0) return;
      const tr = document.createElement('tr');
      tr.style.cssText = idx % 2 === 0 ? 'background:#fff;' : 'background:#f8fdf8;';
      tr.innerHTML = `
        <td style="text-align:left; padding:4px 3px;">${icon} ${name}</td>
        <td style="text-align:center; color:#000;">${qty}</td>
        <td style="text-align:right; padding:4px 3px; font-weight:700; color:#27ae60;">${pts}</td>
      `;
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    body.appendChild(table);

    const hr3 = document.createElement('hr');
    hr3.className = 'receipt-divider';
    body.appendChild(hr3);

    // ── QR code ───────────────────────────────────────────────────────────
    const qrArea = document.createElement('div');
    qrArea.className = 'receipt-qr-area';
    body.appendChild(qrArea);

    if (window.QRCode && qrData) {
      try {
        new QRCode(qrArea, {
          text: qrData,
          width: 130,
          height: 130,
          colorDark: '#000',
          colorLight: '#fff',
          correctLevel: QRCode.CorrectLevel.M,
        });
      } catch (e) {
        qrArea.innerHTML = `<span style="font-size:10px;color:#666;">[QR: ${qrData}]</span>`;
      }
    }

    const ts = document.createElement('div');
    ts.className = 'receipt-timestamp';
    ts.textContent = now;
    body.appendChild(ts);

    if (meta) meta.textContent = `İş ID: ${jobId || '—'}  |  Makine: ${machineId}`;

    setTimeout(() => {
      section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // LOGS
  // ═══════════════════════════════════════════════════════════════════════════

  /**
   * Logları yükle
   */
  async loadLogs(statusFilter = null) {
    try {
      const params = { page: 1, page_size: 1000 };
      if (statusFilter) params.status = statusFilter;
      const result = await api.getLogs(params);
      this.renderLogs(result.entries || [], result.total || 0);
    } catch (error) {
      console.error('Failed to load logs:', error);
    }
  }

  /**
   * Logları render et
   */
  renderLogs(entries, total) {
    const tbody = document.getElementById('logsTableBody');
    if (!tbody) return;

    // Toplam sayacı güncelle
    const totalEl = document.getElementById('logsTotalCount');
    if (totalEl) totalEl.textContent = `(${total} kayıt)`;

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
      const isFailed = entry.status === 'failed';
      const statusClass = entry.status === 'done' ? 'success' :
                         isFailed ? 'error' : 'secondary';

      const time = entry.ts ? new Date(entry.ts).toLocaleString('tr-TR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      }) : '—';

      const jobIdShort = entry.job_id ? entry.job_id.substring(0, 12) + '...' : '—';
      const errorText = entry.error
        ? `<strong>${entry.error.code || ''}</strong> ${entry.error.detail || ''}`.trim()
        : '';

      // Hatalı satırları farklı arka plan ile vurgula
      const rowStyle = isFailed
        ? 'background: rgba(239,68,68,0.06); border-left: 3px solid #ef4444;'
        : '';

      return `
        <tr style="${rowStyle}">
          <td class="font-mono text-secondary" style="font-size: 11px; white-space: nowrap;">${time}</td>
          <td>${entry.op || '—'}</td>
          <td class="font-mono" style="font-size: 11px;">${jobIdShort}</td>
          <td><span class="badge badge-${statusClass}">${entry.status}</span></td>
          <td class="text-error" style="font-size: 11px;">${errorText}</td>
        </tr>
      `;
    }).join('');
  }

  /**
   * Log otomatik yenilemeyi başlat (30 saniye)
   */
  startLogAutoRefresh() {
    if (this.logRefreshInterval) return;
    this.logRefreshInterval = setInterval(() => {
      const activeFilter = document.getElementById('logFilterSelect')?.value || null;
      this.loadLogs(activeFilter === 'all' ? null : activeFilter);
    }, 30000);
  }

  stopLogAutoRefresh() {
    if (this.logRefreshInterval) {
      clearInterval(this.logRefreshInterval);
      this.logRefreshInterval = null;
    }
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
    this.stopLogAutoRefresh();
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
