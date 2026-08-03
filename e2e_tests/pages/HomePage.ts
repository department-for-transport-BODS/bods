import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class HomePage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to the home page
   */
  async navigate(): Promise<this> {
    return await this.navigateTo('/');
  }

  /**
   * Verify on the home page
   */
  async verifyOnPage(): Promise<this> {
    const url = this.getUrl();
    expect(url).toContain(this.baseUrl);
    return this;
  }

  /**
   * Verify the page title
   */
  async verifyTitle(expectedTitle: string): Promise<this> {
    const actual = await this.getTitle();
    expect(actual).toContain(expectedTitle);
    return this;
  }

  /**
   * Click the login/sign in button
   */
  async clickLogin(selector: string = 'text=Sign in'): Promise<this> {
    await this.click(selector);
    return this;
  }
}
