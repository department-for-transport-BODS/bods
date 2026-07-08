import { defineConfig, devices } from '@playwright/test';
import { config } from './config';
import { AUTH_STATE_PATH } from './global-setup';

export default defineConfig({
  testDir: './',
  testMatch: '*.spec.ts',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? [['github'], ['html'], ['list']] : [['html'], ['list']],
  timeout: 120000,
  globalSetup: './global-setup.ts',
  use: {
    baseURL: config.baseUrl,
    storageState: AUTH_STATE_PATH,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: config.defaultTimeoutMs,
    navigationTimeout: config.navigationTimeoutMs,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});