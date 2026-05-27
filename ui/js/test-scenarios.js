/**
 * Test Scenarios Definition
 * Defines all test scenarios for the simulation panel
 */

const TEST_SCENARIOS = {
  categories: [
    {
      id: 'basic_errors',
      nameKey: 'testSimulation.categories.basicErrors',
      tests: [
        {
          id: 'paper_out',
          nameKey: 'testSimulation.tests.paperOut',
          descKey: 'testSimulation.tests.paperOutDesc',
          steps: [
            { action: 'simulate', error: 'PAPER_OUT', operations: -1 },
            { action: 'print_text', expectStatus: 503 },
            { action: 'check_status', expectData: { paper_ok: false, error_code: 'PAPER_OUT' } },
            { action: 'clear_simulation' }
          ]
        },
        {
          id: 'paper_jam',
          nameKey: 'testSimulation.tests.paperJam',
          descKey: 'testSimulation.tests.paperJamDesc',
          steps: [
            { action: 'simulate', error: 'PAPER_JAM', operations: -1 },
            { action: 'print_text', expectStatus: 503 },
            { action: 'check_status', expectData: { paper_ok: false, error_code: 'PAPER_JAM' } },
            { action: 'clear_simulation' }
          ]
        },
        {
          id: 'cover_open',
          nameKey: 'testSimulation.tests.coverOpen',
          descKey: 'testSimulation.tests.coverOpenDesc',
          steps: [
            { action: 'simulate', error: 'COVER_OPEN', operations: -1 },
            { action: 'print_text', expectStatus: 503 },
            { action: 'check_status', expectData: { cover_ok: false, error_code: 'COVER_OPEN' } },
            { action: 'clear_simulation' }
          ]
        },
        {
          id: 'overheat',
          nameKey: 'testSimulation.tests.overheat',
          descKey: 'testSimulation.tests.overheatDesc',
          steps: [
            { action: 'simulate', error: 'OVERHEAT', operations: -1 },
            { action: 'print_text', expectStatus: 503 },
            { action: 'check_status', expectData: { temperature_ok: false, error_code: 'OVERHEAT' } },
            { action: 'clear_simulation' }
          ]
        },
        {
          id: 'comm_error',
          nameKey: 'testSimulation.tests.commError',
          descKey: 'testSimulation.tests.commErrorDesc',
          steps: [
            { action: 'simulate', error: 'COMM_ERROR', operations: -1 },
            { action: 'print_text', expectStatus: 502 },
            { action: 'clear_simulation' }
          ]
        },
        {
          id: 'unknown_command',
          nameKey: 'testSimulation.tests.unknownCommand',
          descKey: 'testSimulation.tests.unknownCommandDesc',
          steps: [
            { action: 'simulate', error: 'UNKNOWN_COMMAND', operations: -1 },
            { action: 'print_text', expectStatus: 400 },
            { action: 'clear_simulation' }
          ]
        }
      ]
    },
    {
      id: 'api_integration',
      nameKey: 'testSimulation.categories.apiIntegration',
      tests: [
        {
          id: 'api_print_paper_out',
          nameKey: 'testSimulation.tests.apiPrintPaperOut',
          descKey: 'testSimulation.tests.apiPrintPaperOutDesc',
          steps: [
            { action: 'simulate', error: 'PAPER_OUT', operations: -1 },
            { action: 'print_text', expectStatus: 503 },
            { action: 'clear_simulation' },
            { action: 'print_text', expectStatus: 200 }
          ]
        },
        {
          id: 'api_print_cover_open',
          nameKey: 'testSimulation.tests.apiPrintCoverOpen',
          descKey: 'testSimulation.tests.apiPrintCoverOpenDesc',
          steps: [
            { action: 'simulate', error: 'COVER_OPEN', operations: -1 },
            { action: 'print_text', expectStatus: 503 },
            { action: 'clear_simulation' },
            { action: 'print_text', expectStatus: 200 }
          ]
        },
        {
          id: 'api_status_reflects',
          nameKey: 'testSimulation.tests.apiStatusReflects',
          descKey: 'testSimulation.tests.apiStatusReflectsDesc',
          steps: [
            { action: 'simulate', error: 'PAPER_JAM', operations: -1 },
            { action: 'check_status', expectData: { error_code: 'PAPER_JAM' } },
            { action: 'clear_simulation' },
            { action: 'check_status', expectData: { error_code: null } }
          ]
        }
      ]
    },
    {
      id: 'realistic_scenarios',
      nameKey: 'testSimulation.categories.realisticScenarios',
      tests: [
        {
          id: 'intermittent_jam',
          nameKey: 'testSimulation.tests.intermittentJam',
          descKey: 'testSimulation.tests.intermittentJamDesc',
          steps: [
            { action: 'simulate', error: 'PAPER_JAM', operations: 2 },
            { action: 'print_text', expectStatus: 503 },
            { action: 'print_text', expectStatus: 503 },
            { action: 'print_text', expectStatus: 200 }
          ]
        },
        {
          id: 'error_recovery',
          nameKey: 'testSimulation.tests.errorRecovery',
          descKey: 'testSimulation.tests.errorRecoveryDesc',
          steps: [
            { action: 'simulate', error: 'PAPER_OUT', operations: -1 },
            { action: 'print_text', expectStatus: 503 },
            { action: 'clear_simulation' },
            { action: 'print_text', expectStatus: 200 },
            { action: 'check_status', expectData: { paper_ok: true, error_code: null } }
          ]
        }
      ]
    },
    {
      id: 'limited_ops',
      nameKey: 'testSimulation.categories.limitedOps',
      tests: [
        {
          id: 'limited_operations',
          nameKey: 'testSimulation.tests.limitedOperations',
          descKey: 'testSimulation.tests.limitedOperationsDesc',
          steps: [
            { action: 'simulate', error: 'COVER_OPEN', operations: 3 },
            { action: 'print_text', expectStatus: 503 },
            { action: 'print_text', expectStatus: 503 },
            { action: 'print_text', expectStatus: 503 },
            { action: 'print_text', expectStatus: 200 }
          ]
        }
      ]
    }
  ]
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = TEST_SCENARIOS;
}
