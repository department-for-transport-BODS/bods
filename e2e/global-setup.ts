import { chromium, FullConfig } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';
import { config } from './config';
import { login } from './utils/auth';

export const AUTH_STATE_PATH = '.auth/user.json';

export default async function globalSetup(_config: FullConfig): Promise<void> {
  if (!config.baseUrl) {
    throw new Error('PLAYWRIGHT_BASE_URL must be configured.');
  }

  if (!config.testUser.username || !config.testUser.password) {
    // No credentials provided. Authenticated tests will fail in fixture with a clear message.
    return;
  }

  const authDir = path.resolve(__dirname, '.auth');
  const authFile = path.resolve(__dirname, AUTH_STATE_PATH);
  await mkdir(authDir, { recursive: true });

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    await login(page, config.baseUrl, config.testUser.username, config.testUser.password);
    await page.context().storageState({ path: authFile });
  } finally {
    await browser.close();
  }
}