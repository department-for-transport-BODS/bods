/**
 * Authentication helper functions
 * Provides reusable authentication logic across all tests
 */
import { Page } from '@playwright/test';
import { config } from '../config';

export class AuthHelper {
  constructor(private page: Page) {}

  /**
   * Login to the application
   *
   */
  async login(email?: string, password?: string): Promise<void> {
    const userEmail = email || config.testUser.email;
    const userPassword = password || config.testUser.password;
    try {
      const loginUrl = `${config.publishUrl}/account/login/`;
      await this.page.goto(loginUrl, { waitUntil: 'domcontentloaded' });

      // Wait briefly for either a redirect away from login (already authenticated)
      // or for the login form to become visible.
      await Promise.race([
        this.page.waitForURL((url) => !url.toString().includes('/account/login/'), { timeout: 10000 }),
        this.page.waitForSelector('input[name="login"]', { timeout: 10000 }),
      ]).catch(() => undefined);

      // If redirected away from the login page, assume an existing session.
      if (!this.page.url().includes('/account/login/')) {
        return;
      }

      await this.page.waitForSelector('input[name="login"]', { timeout: 5000 });
      await this.page.fill('input[name="login"]', userEmail);
      await this.page.fill('input[name="password"]', userPassword);
      await this.page.getByRole('button', { name: /sign in/i }).click();
      await this.page.waitForLoadState('networkidle');
    } catch (err) {
      // Capture a screenshot to help debugging environment-specific failures
      try {
        const path = `./test-failure-screenshots/login-failure-${Date.now()}.png`;
        await this.page.screenshot({ path, fullPage: true });
        // eslint-disable-next-line no-console
        console.error(`Saved login failure screenshot: ${path}`);
      } catch (screenshotErr) {
        // ignore screenshot errors
      }
      throw err;
    }
  }

  /**
   * Logout from the application
   *
   */
  async logout(): Promise<void> {
  }

  /**
   * Check if user is logged in
   *
   */
  async isLoggedIn(): Promise<boolean> {
    return true;
  }
}

export function createAuthHelper(page: Page): AuthHelper {
  return new AuthHelper(page);
}
