import { Page } from '@playwright/test';
import { config } from '../config';

export class BasePage {
  protected page: Page;
  protected baseUrl: string;

  constructor(page: Page) {
    this.page = page;
    this.baseUrl = config.baseUrl;
  }

  async navigateTo(path: string = ''): Promise<this> {
    const url = `${this.baseUrl}${path}`;
    await this.page.goto(url);
    return this;
  }

  async getTitle(): Promise<string> {
    return await this.page.title();
  }

  getUrl(): string {
    return this.page.url();
  }

  async waitForSelector(selector: string, timeout?: number): Promise<this> {
    await this.page.waitForSelector(selector, {
      timeout: timeout || config.defaultTimeout
    });
    return this;
  }

  async click(selector: string): Promise<this> {
    await this.page.click(selector);
    return this;
  }


  async fill(selector: string, value: string): Promise<this> {
    await this.page.fill(selector, value);
    return this;
  }

  async isVisible(selector: string): Promise<boolean> {
    return await this.page.isVisible(selector);
  }

  async screenshot(path?: string): Promise<Buffer | void> {
    if (path) {
      await this.page.screenshot({ path });
    } else {
      return await this.page.screenshot();
    }
  }

  async waitForLoadState(state: 'load' | 'domcontentloaded' | 'networkidle' = 'load'): Promise<this> {
    await this.page.waitForLoadState(state);
    return this;
  }

  /**
   * Navigate to the page - should be overridden by subclasses
   */
  async navigate(...args: any[]): Promise<this> {
    return await this.navigateTo('/');
  }

  /**
   * Verify that on the correct page - should be overridden by subclasses
   */
  async verifyOnPage(): Promise<this> {
    // Base implementation does nothing, subclasses should override
    return this;
  }

  /**
   * Check if the page has loaded successfully - should be overridden by subclasses
   */
  async hasLoaded(): Promise<boolean> {
    await this.waitForLoadState('networkidle');
    return true;
  }
}
