import { defineConfig, devices } from '@playwright/test';
import { config } from './config';

/**
 * Playwright configuration
 * See https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests',

  /* Run tests in files in parallel */
  fullyParallel: true,

  /* Fail the build on CI if you accidentally left test.only in the source code */
  forbidOnly: !!process.env.CI,

  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,

  /* Opt out of parallel tests on CI */
  workers: process.env.CI ? 1 : undefined,

  /* Reporter to use */
  reporter: process.env.CI
    ? [['html'], ['github'], ['list']]
    : [['html'], ['list']],

  /* Shared settings for all the projects below */
  use: {
    /* Base URL */
    baseURL: config.baseUrl,

    ignoreHTTPSErrors: process.env.IGNORE_HTTPS_ERRORS === 'true' || false,


    trace: 'on-first-retry',

    screenshot: process.env.CI ? 'only-on-failure' : 'on',

    video: process.env.CI ? 'retain-on-failure' : 'on',

    /* Timeouts */
    actionTimeout: config.defaultTimeout,
    navigationTimeout: config.navigationTimeout,
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    }
  ]
});
