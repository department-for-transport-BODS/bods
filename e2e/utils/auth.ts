import { expect, Page } from '@playwright/test';

export async function login(page: Page, baseUrl: string, username: string, password: string): Promise<void> {
  await page.goto(`${baseUrl}/account/login/`, { waitUntil: 'domcontentloaded' });

  // Prefer accessible locators so auth is resilient to form markup changes.
  await page.getByLabel(/email/i).fill(username);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole('button', { name: /sign in/i }).click();
  await page.waitForLoadState('networkidle');

  const stillOnLogin = /\/account\/login\/?$/.test(page.url());
  if (stillOnLogin) {
    const throttleMessage = page.getByText(/Request was throttled/i);
    if (await throttleMessage.isVisible()) {
      const details = (await throttleMessage.textContent())?.trim() || 'Request was throttled.';
      throw new Error(
        `Login throttled by the service: ${details} Re-run after the throttle window or reuse an existing auth session.`,
      );
    }
  }

  // Login page remains if auth fails.
  await expect(page).not.toHaveURL(/\/account\/login\/?$/);
}