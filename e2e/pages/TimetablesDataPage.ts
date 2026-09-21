/**
 * Timetables Data browsing page object
 * Route: /data/timetables
 */
import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class TimetablesDataPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async navigate(): Promise<this> {
    return await this.navigateTo('/data/timetables?status=live');
  }

  async verifyOnPage(): Promise<this> {
    expect(this.page.url()).toContain('/data/timetables');
    return this;
  }

  async hasLoaded(): Promise<boolean> {
    await this.page.waitForLoadState('networkidle');
    return this.page.url().includes('/data/timetables');
  }

  async getHeading(): Promise<string | null> {
    return await this.page.locator('h1').textContent();
  }

  async hasSearchInput(): Promise<boolean> {
    return await this.page.locator('input[type="search"], input[type="text"]').first().isVisible();
  }

  async searchFor(query: string): Promise<this> {
    const searchInput = this.page.locator('input[type="search"], input[type="text"]').first();
    await searchInput.fill(query);
    return this;
  }

  async getResultCount(): Promise<number> {
    const rows = this.page.locator('table tbody tr, .govuk-table__body .govuk-table__row');
    return await rows.count();
  }

  async hasMainContent(): Promise<boolean> {
    return await this.page.locator('#main-content, main').first().isVisible();
  }
}
