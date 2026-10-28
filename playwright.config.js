const { defineConfig } = require('@playwright/test');
const python = process.env.E2E_PYTHON ? require('path').resolve(process.env.E2E_PYTHON) : 'python';
module.exports = defineConfig({
  testDir: './tests/e2e', workers: 1, retries: process.env.CI ? 1 : 0,
  reporter: [['list'], ['html', {open:'never'}], ['junit', {outputFile:'test-results/web.xml'}]],
  use: {baseURL:'http://127.0.0.1:18765', trace:'retain-on-failure', screenshot:'only-on-failure'},
  webServer: {
    command: `"${python}" tests/support/e2e_server.py`,
    url:'http://127.0.0.1:18765/api/auth/status', reuseExistingServer:false,
    env:{EXPENSA_E2E:'1'}, timeout:60000
  }
});
