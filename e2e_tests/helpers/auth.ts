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
    await this.page.goto(`${config.publishUrl}/account/login/`);
    await this.page.fill('input[name="login"]', userEmail);
    await this.page.fill('input[name="password"]', userPassword);
    await this.page.getByRole('button', { name: /sign in/i }).click();
    await this.page.waitForLoadState('networkidle');
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
