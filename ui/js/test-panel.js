/**
 * Test Simulation Panel Manager
 * Renders and manages the test simulation UI
 */

class TestSimulationPanel {
  constructor() {
    this.testRunner = new TestRunner();
    this.container = null;
    this.expandedCategories = new Set();
  }

  /**
   * Initialize the panel
   */
  async init() {
    this.container = document.getElementById('testSimulationPanel');
    if (!this.container) return;

    // Initialize test runner with scenarios
    this.testRunner.init(TEST_SCENARIOS);
    
    // Set update callback
    this.testRunner.onUpdate = (state) => this.render(state);

    // Initial render
    this.render({
      tests: this.testRunner.tests,
      results: this.testRunner.results,
      isRunning: false,
      currentTest: null
    });
  }

  /**
   * Render the entire panel
   */
  render(state) {
    if (!this.container) return;

    const { tests, results, isRunning, currentTest } = state;

    this.container.innerHTML = `
      ${this.renderHeader(isRunning)}
      ${this.renderProgress(results, tests.length)}
      ${this.renderCategories(tests, currentTest)}
    `;

    // Attach event listeners
    this.attachEventListeners();
    
    // Update i18n
    if (window.i18n) {
      i18n.updateUI();
    }
  }

  /**
   * Render panel header
   */
  renderHeader(isRunning) {
    return `
      <div class="test-panel">
        <div class="test-panel-header">
          <div>
            <h2 class="test-panel-title" data-i18n="testSimulation.title">🧪 Test Simülasyon Paneli</h2>
            <p class="test-panel-subtitle" data-i18n="testSimulation.subtitle">Tüm hata senaryolarını canlı test edin</p>
          </div>
          <div class="test-panel-actions">
            <button class="btn-test btn-test-primary" id="runAllTestsBtn" ${isRunning ? 'disabled' : ''}>
              <span data-i18n="testSimulation.runAll">▶ Tüm Testleri Çalıştır</span>
            </button>
            <button class="btn-test btn-test-danger" id="stopTestsBtn" ${!isRunning ? 'disabled' : ''}>
              <span data-i18n="testSimulation.stop">⏹ Durdur</span>
            </button>
            <button class="btn-test btn-test-secondary" id="clearTestsBtn" ${isRunning ? 'disabled' : ''}>
              <span data-i18n="testSimulation.clear">🗑 Temizle</span>
            </button>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Render progress bar
   */
  renderProgress(results, total) {
    const completed = results.passed + results.failed;
    const progressPercent = total > 0 ? (completed / total) * 100 : 0;

    return `
      <div class="test-panel">
        <div class="test-progress">
          <div class="test-progress-bar">
            <div class="test-progress-fill" style="width: ${progressPercent}%"></div>
          </div>
          <div class="test-progress-stats">
            <div class="test-stat">
              <span data-i18n="testSimulation.progress">İlerleme</span>:
              <span class="test-stat-value">${completed}/${total}</span>
            </div>
            <div class="test-stat success">
              <span>✓</span>
              <span class="test-stat-value">${results.passed}</span>
              <span data-i18n="testSimulation.successful">Başarılı</span>
            </div>
            <div class="test-stat failed">
              <span>✗</span>
              <span class="test-stat-value">${results.failed}</span>
              <span data-i18n="testSimulation.failed">Başarısız</span>
            </div>
            <div class="test-stat pending">
              <span>⏳</span>
              <span class="test-stat-value">${results.pending}</span>
              <span data-i18n="testSimulation.pending">Bekliyor</span>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  /**
   * Render test categories
   */
  renderCategories(tests, currentTest) {
    const categories = TEST_SCENARIOS.categories;
    
    return `
      <div class="test-panel">
        ${categories.map(category => this.renderCategory(category, tests, currentTest)).join('')}
      </div>
    `;
  }

  /**
   * Render a single category
   */
  renderCategory(category, allTests, currentTest) {
    const categoryTests = allTests.filter(t => t.categoryId === category.id);
    const passed = categoryTests.filter(t => t.status === 'passed').length;
    const failed = categoryTests.filter(t => t.status === 'failed').length;
    const isExpanded = this.expandedCategories.has(category.id);

    return `
      <div class="test-category ${isExpanded ? 'expanded' : ''}" data-category-id="${category.id}">
        <div class="test-category-header" data-toggle-category="${category.id}">
          <div class="test-category-title">
            <span>${isExpanded ? '▼' : '▶'}</span>
            <span data-i18n="${category.nameKey}">${category.nameKey}</span>
            <span class="test-category-badge">${categoryTests.length}</span>
            ${passed > 0 ? `<span style="color: #10b981;">✓${passed}</span>` : ''}
            ${failed > 0 ? `<span style="color: #ef4444;">✗${failed}</span>` : ''}
          </div>
          <button class="btn-test btn-test-sm btn-test-secondary" data-run-category="${category.id}">
            <span data-i18n="testSimulation.runCategory">▶ Kategoriyi Çalıştır</span>
          </button>
        </div>
        <div class="test-category-body">
          ${categoryTests.map(test => this.renderTest(test, currentTest)).join('')}
        </div>
      </div>
    `;
  }

  /**
   * Render a single test
   */
  renderTest(test, currentTest) {
    const isCurrentTest = currentTest && currentTest.id === test.id;
    const statusIcon = this.getStatusIcon(test.status);
    const duration = test.duration > 0 ? `${(test.duration / 1000).toFixed(2)}s` : '';

    return `
      <div class="test-item">
        <div class="test-item-info">
          <div class="test-item-name">
            ${statusIcon}
            <span data-i18n="${test.nameKey}">${test.nameKey}</span>
          </div>
          <div class="test-item-desc" data-i18n="${test.descKey}">${test.descKey}</div>
          ${test.error ? `<div class="test-step-error">${test.error}</div>` : ''}
          ${test.stepResults.length > 0 ? this.renderTestDetails(test) : ''}
        </div>
        <div class="test-item-actions">
          ${duration ? `<span class="test-item-duration">${duration}</span>` : ''}
          <button class="btn-test btn-test-sm btn-test-secondary" data-run-test="${test.id}" ${isCurrentTest ? 'disabled' : ''}>
            <span data-i18n="testSimulation.runTest">▶ Çalıştır</span>
          </button>
        </div>
      </div>
    `;
  }

  /**
   * Render test details (steps)
   */
  renderTestDetails(test) {
    if (test.stepResults.length === 0) return '';

    return `
      <div class="test-details">
        <div class="test-details-header" data-i18n="testSimulation.details">Detaylar</div>
        ${test.stepResults.map((step, idx) => `
          <div class="test-step ${step.success ? 'success' : 'failed'}">
            <div class="test-step-action">
              ${idx + 1}. ${step.action} ${step.success ? '✓' : '✗'}
            </div>
            ${step.error ? `<div class="test-step-error">${step.error}</div>` : ''}
          </div>
        `).join('')}
      </div>
    `;
  }

  /**
   * Get status icon HTML
   */
  getStatusIcon(status) {
    const icons = {
      pending: '⏳',
      running: '🔄',
      passed: '✓',
      failed: '✗'
    };
    return `<span class="test-status-icon ${status}">${icons[status] || '⏳'}</span>`;
  }

  /**
   * Attach event listeners
   */
  attachEventListeners() {
    // Run all tests
    const runAllBtn = document.getElementById('runAllTestsBtn');
    if (runAllBtn) {
      runAllBtn.onclick = () => this.testRunner.runAll();
    }

    // Stop tests
    const stopBtn = document.getElementById('stopTestsBtn');
    if (stopBtn) {
      stopBtn.onclick = () => this.testRunner.stop();
    }

    // Clear tests
    const clearBtn = document.getElementById('clearTestsBtn');
    if (clearBtn) {
      clearBtn.onclick = () => this.testRunner.clear();
    }

    // Toggle category
    document.querySelectorAll('[data-toggle-category]').forEach(el => {
      el.onclick = (e) => {
        if (e.target.closest('[data-run-category]')) return; // Don't toggle if clicking run button
        const categoryId = el.dataset.toggleCategory;
        if (this.expandedCategories.has(categoryId)) {
          this.expandedCategories.delete(categoryId);
        } else {
          this.expandedCategories.add(categoryId);
        }
        this.render({
          tests: this.testRunner.tests,
          results: this.testRunner.results,
          isRunning: this.testRunner.isRunning,
          currentTest: this.testRunner.currentTest
        });
      };
    });

    // Run category
    document.querySelectorAll('[data-run-category]').forEach(el => {
      el.onclick = (e) => {
        e.stopPropagation();
        const categoryId = el.dataset.runCategory;
        this.testRunner.runCategory(categoryId);
      };
    });

    // Run single test
    document.querySelectorAll('[data-run-test]').forEach(el => {
      el.onclick = () => {
        const testId = el.dataset.runTest;
        const test = this.testRunner.getTest(testId);
        if (test) {
          this.testRunner.runTest(test);
        }
      };
    });
  }
}

// Initialize when DOM is ready
let testPanel;
document.addEventListener('DOMContentLoaded', () => {
  testPanel = new TestSimulationPanel();
  testPanel.init();
});

// Export
window.testPanel = testPanel;
