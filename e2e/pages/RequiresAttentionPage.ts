/**
 * Service codes requiring attention page object, shared by the timetable and fares journeys.
 * Routes:
 *   /publish/org/[orgId]/dataset/timetable/attention
 *   /publish/org/[orgId]/dataset/fares/attention
 */
import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export type RequiresAttentionKind = 'timetable' | 'fares';

export class RequiresAttentionPage extends BasePage {
  private readonly kind: RequiresAttentionKind;

  constructor(page: Page, kind: RequiresAttentionKind) {
    super(page);
    this.kind = kind;
  }

  async navigate(orgId: string, query = ''): Promise<this> {
    const suffix = query ? `?q=${encodeURIComponent(query)}` : '';
    return await this.navigateTo(`/publish/org/${orgId}/dataset/${this.kind}/attention${suffix}`);
  }

  async verifyOnPage(): Promise<this> {
    expect(this.page.url()).toContain(`/dataset/${this.kind}/attention`);
    return this;
  }

  heading() {
    return this.page.getByRole('heading', { level: 1, name: 'Service codes requiring attention' });
  }

  searchBox() {
    return this.page.getByRole('searchbox');
  }

  table() {
    return this.page.getByRole('table');
  }

  emptyStateHeading() {
    return this.page.getByRole('heading', { name: 'Sorry, no results found for your search' });
  }

  exportLink() {
    return this.page.getByRole('link', { name: 'Download detailed export' });
  }

  sortLink(column: 'Licence number' | 'Service code' | 'Line') {
    return this.page.getByRole('button', { name: new RegExp(`^${column}`) });
  }

  async search(term: string): Promise<this> {
    await this.searchBox().fill(term);
    await this.searchBox().press('Enter');
    return this;
  }

  async openLineHelp(): Promise<this> {
    await this.page.getByRole('button', { name: 'Help' }).click();
    return this;
  }
}
