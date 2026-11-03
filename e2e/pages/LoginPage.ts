import { expect, type Locator, type Page } from '@playwright/test';
import { BasePage } from './BasePage';

export class LoginPage extends BasePage {
  readonly emailInput: Locator;
  readonly passwordInput: Locator;

  constructor(page: Page) {
    super(page);
    this.emailInput = page.getByLabel('Email*');
    this.passwordInput = page.getByLabel('Password*');
  }

  async navigate(): Promise<this> {
    return this.navigateTo('/account/login');
  }

  async submit(): Promise<this> {
    await this.page.getByRole('button', { name: 'Sign In' }).click();
    return this;
  }

  async verifyOnPage(): Promise<this> {
    await expect(this.page.getByRole('heading', { name: 'Sign in', level: 1 }))
      .toBeVisible();
    return this;
  }
}
