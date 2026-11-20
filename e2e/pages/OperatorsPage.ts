/**
 * Operator Profiles list page object
 * Route: /data/operators  (public URL on the data host: /operators/)
 * Django source: transit_odp/browse/templates/browse/operators.html
 */
import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class OperatorsPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async navigate(query = ''): Promise<this> {
    return await this.navigateTo(`/data/operators${query}`);
  }

  async verifyOnPage(): Promise<this> {
    await expect(this.page.getByRole('heading', { level: 1, name: 'Operator Profiles' })).toBeVisible();
    return this;
  }

  get searchInput() {
    return this.page.getByPlaceholder('Enter operator name');
  }

  get sortSelect() {
    return this.page.getByLabel('Sort by');
  }

  get resultsSummary() {
    return this.page.getByText(/^\d[\d,]* results?$/);
  }

  operatorLink(name: string) {
    return this.page.getByRole('link', { name, exact: true });
  }

  async searchFor(term: string): Promise<this> {
    await this.searchInput.fill(term);
    await this.searchInput.press('Enter');
    return this;
  }

  async sortBy(label: string): Promise<this> {
    await this.sortSelect.selectOption({ label });
    return this;
  }

  async openFirstOperator(): Promise<string> {
    const link = this.page.locator('main a[href*="/operators/"]').first();
    await expect(link).toBeVisible();
    const name = (await link.textContent())?.trim() ?? '';
    await link.click();
    await this.page.waitForURL(/\/operators\/\d+\/?$/);
    return name;
  }
}
