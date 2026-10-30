/**
 * Local Transport Authority profiles page object (data host)
 * Routes: /local-authority/ and /local-authority/detail/?auth_ids=...
 */
import { Page, Locator, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class LocalAuthorityPage extends BasePage {
  readonly heading: Locator;
  readonly searchInput: Locator;
  readonly sortSelect: Locator;
  readonly resultLinks: Locator;
  readonly breadcrumbs: Locator;

  constructor(page: Page) {
    super(page);
    this.heading = page.locator('h1');
    this.searchInput = page.getByPlaceholder('Enter Local Transport Authority name');
    this.sortSelect = page.getByLabel('Sort by');
    this.resultLinks = page.locator('a[href*="/local-authority/detail"]');
    this.breadcrumbs = page.getByRole('navigation', { name: 'Breadcrumb' });
  }

  async navigate(query = ''): Promise<this> {
    return await this.navigateTo(`/data/local-authority${query}`);
  }

  async search(term: string): Promise<this> {
    await this.searchInput.fill(term);
    await this.searchInput.press('Enter');
    return this;
  }

  async openFirstAuthority(): Promise<this> {
    await this.resultLinks.first().click();
    return this;
  }

  async verifyOnListPage(): Promise<this> {
    await expect(this.heading).toHaveText('Local Transport Authority');
    await expect(this.breadcrumbs).toContainText('Local Transport Authority Profiles');
    return this;
  }
}
