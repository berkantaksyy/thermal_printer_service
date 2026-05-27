/**
 * Test Runner
 * Executes test scenarios and manages test state
 */

class TestRunner {
  constructor() {
    this.tests = [];
    this.currentTest = null;
    this.isRunning = false;
    this.results = {
      total: 0,
      passed: 0,
      failed: 0,
      pending: 0
    };
    this.onUpdate = null; // Callback for UI updates
  }

  /**
   * Initialize test runner with scenarios
   */
  init(scenarios) {
    this.tests = [];
    
    scenarios.categories.forEach(category => {
      category.tests.forEach(test => {
        this.tests.push({
          id: test.id,
          categoryId: category.id,
          nameKey: test.nameKey,
          descKey: test.descKey,
          steps: test.steps,
          status: 'pending', // pending, running, passed, failed
          duration: 0,
          error: null,
          stepResults: []
        });
      });
    });

    this.results.total = this.tests.length;
    this.results.pending = this.tests.length;
    this.results.passed = 0;
    this.results.failed = 0;
  }

  /**
   * Run all tests
   */
  async runAll() {
    if (this.isRunning) return;
    
    this.isRunning = true;
    this.notifyUpdate();

    for (const test of this.tests) {
      if (!this.isRunning) break; // Stop if user clicked stop
      await this.runTest(test);
      await this.sleep(500); // Small delay between tests
    }

    this.isRunning = false;
    this.notifyUpdate();
  }

  /**
   * Run tests in a specific category
   */
  async runCategory(categoryId) {
    if (this.isRunning) return;
    
    this.isRunning = true;
    this.notifyUpdate();

    const categoryTests = this.tests.filter(t => t.categoryId === categoryId);
    
    for (const test of categoryTests) {
      if (!this.isRunning) break;
      await this.runTest(test);
      await this.sleep(500);
    }

    this.isRunning = false;
    this.notifyUpdate();
  }

  /**
   * Run a single test
   */
  async runTest(test) {
    this.currentTest = test;
    test.status = 'running';
    test.error = null;
    test.stepResults = [];
    
    const startTime = Date.now();
    this.notifyUpdate();

    try {
      // Execute each step
      for (let i = 0; i < test.steps.length; i++) {
        const step = test.steps[i];
        const stepResult = await this.executeStep(step, i + 1, test.steps.length);
        test.stepResults.push(stepResult);

        if (!stepResult.success) {
          throw new Error(stepResult.error);
        }

        await this.sleep(300); // Small delay between steps
      }

      // All steps passed
      test.status = 'passed';
      this.results.passed++;
      this.results.pending--;
      
    } catch (error) {
      test.status = 'failed';
      test.error = error.message;
      this.results.failed++;
      this.results.pending--;
    }

    test.duration = Date.now() - startTime;
    this.currentTest = null;
    this.notifyUpdate();
  }

  /**
   * Execute a single test step
   */
  async executeStep(step, stepNum, totalSteps) {
    const result = {
      step: stepNum,
      action: step.action,
      success: false,
      error: null,
      response: null
    };

    try {
      switch (step.action) {
        case 'simulate':
          result.response = await this.actionSimulate(step.error, step.operations);
          result.success = result.response.status === 200;
          break;

        case 'clear_simulation':
          result.response = await this.actionClearSimulation();
          result.success = result.response.status === 200;
          break;

        case 'print_text':
          result.response = await this.actionPrintText();
          result.success = result.response.status === step.expectStatus;
          if (!result.success) {
            result.error = `Expected status ${step.expectStatus}, got ${result.response.status}`;
          }
          break;

        case 'check_status':
          result.response = await this.actionCheckStatus();
          result.success = this.validateStatusData(result.response.data, step.expectData);
          if (!result.success) {
            result.error = `Status validation failed. Expected: ${JSON.stringify(step.expectData)}`;
          }
          break;

        default:
          result.error = `Unknown action: ${step.action}`;
      }

    } catch (error) {
      result.success = false;
      result.error = error.message;
    }

    return result;
  }

  /**
   * Action: Simulate error
   */
  async actionSimulate(errorType, operations) {
    const response = await api.post('/simulate', {
      error_type: errorType,
      operations: operations
    });
    return { status: response.status, data: response.data };
  }

  /**
   * Action: Clear simulation
   */
  async actionClearSimulation() {
    const response = await api.post('/simulate', {
      error_type: null,
      operations: 0
    });
    return { status: response.status, data: response.data };
  }

  /**
   * Action: Print text
   */
  async actionPrintText() {
    try {
      const response = await api.post('/print/text', {
        lines: [
          { text: 'Test Print', bold: false, align: 'left', font_size: 'normal' }
        ],
        cut: false
      });
      return { status: response.status, data: response.data };
    } catch (error) {
      // API returns error status codes, capture them
      return { 
        status: error.response?.status || 500, 
        data: error.response?.data || { error: error.message }
      };
    }
  }

  /**
   * Action: Check status
   */
  async actionCheckStatus() {
    const response = await api.get('/status');
    return { status: response.status, data: response.data };
  }

  /**
   * Validate status data against expected values
   */
  validateStatusData(actual, expected) {
    for (const key in expected) {
      if (actual[key] !== expected[key]) {
        return false;
      }
    }
    return true;
  }

  /**
   * Stop running tests
   */
  stop() {
    this.isRunning = false;
    if (this.currentTest) {
      this.currentTest.status = 'pending';
    }
    this.notifyUpdate();
  }

  /**
   * Clear all test results
   */
  clear() {
    this.tests.forEach(test => {
      test.status = 'pending';
      test.duration = 0;
      test.error = null;
      test.stepResults = [];
    });

    this.results.passed = 0;
    this.results.failed = 0;
    this.results.pending = this.results.total;
    this.notifyUpdate();
  }

  /**
   * Get test by ID
   */
  getTest(testId) {
    return this.tests.find(t => t.id === testId);
  }

  /**
   * Get tests by category
   */
  getTestsByCategory(categoryId) {
    return this.tests.filter(t => t.categoryId === categoryId);
  }

  /**
   * Get overall results
   */
  getResults() {
    return { ...this.results };
  }

  /**
   * Notify UI of updates
   */
  notifyUpdate() {
    if (this.onUpdate) {
      this.onUpdate({
        tests: this.tests,
        results: this.results,
        isRunning: this.isRunning,
        currentTest: this.currentTest
      });
    }
  }

  /**
   * Sleep utility
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TestRunner;
}
