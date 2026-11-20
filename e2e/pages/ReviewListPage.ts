/**
 * Review my data list page object (timetables, bus location, fares)
 * Route: /publish/org/[orgId]/dataset/{timetable|avl|fares}
 * Mirrors Django's publish_list_base.html.
 */
import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export type ReviewListKind = 'timetable' | 'avl' | 'fares';
export type ReviewListTab = 'active' | 'draft' | 'archive';

const TAB_LABELS: Record<ReviewListTab, string> = {
  active: 'Active',
  draft: 'Draft',
  archive: 'Inactive',
};

export class ReviewListPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async navigate(
    orgId: string,
    kind: ReviewListKind = 'timetable',
    query: string = ''
  ): Promise<this> {
    return await this.navigateTo(
      `/publish/org/${orgId}/dataset/${kind}${query ? `?${query}` : ''}`
    );
  }

  async verifyOnPage(): Promise<this> {
    await expect(this.page.getByRole('heading', { level: 1 })).toContainText('Review');
    await expect(this.page.locator('.review-banner')).toBeVisible();
    return this;
  }

  async hasLoaded(): Promise<boolean> {
    await this.page.waitForLoadState('networkidle');
    return await this.page.locator('.review-banner').isVisible();
  }

  async getHeading(): Promise<string | null> {
    return await this.page.getByRole('heading', { level: 1 }).textContent();
  }

  async bannerStatCount(): Promise<number> {
    return await this.page.locator('.review-banner .review-stat').count();
  }

  async selectTab(tab: ReviewListTab): Promise<this> {
    await this.page.getByRole('link', { name: TAB_LABELS[tab], exact: true }).click();
    await expect(this.page).toHaveURL(new RegExp(`tab=${tab}`));
    return this;
  }

  async selectDataType(label: 'Timetables data' | 'Bus location data' | 'Fares data'): Promise<this> {
    await this.page.getByLabel('Select data type').selectOption({ label });
    return this;
  }

  async columnHeaders(): Promise<string[]> {
    const headers = await this.page.getByRole('columnheader').allTextContents();
    return headers.map((text) => text.replace(/Sort your data by .*/, '').trim());
  }

  async sortBy(columnLabel: string): Promise<this> {
    await this.page
      .getByRole('columnheader', { name: new RegExp(columnLabel) })
      .getByRole('button')
      .click();
    return this;
  }

  async sortedColumn(): Promise<{ label: string; direction: string } | null> {
    const header = this.page.locator('th[aria-sort="ascending"], th[aria-sort="descending"]').first();
    if ((await header.count()) === 0) {
      return null;
    }
    const direction = (await header.getAttribute('aria-sort')) ?? '';
    const text = (await header.textContent()) ?? '';
    return { label: text.replace(/Sort your data by .*/, '').trim(), direction };
  }

  async rowCount(): Promise<number> {
    return await this.page.locator('table.custom_govuk_table tbody tr').count();
  }

  async hasNoDataMessage(): Promise<boolean> {
    return await this.page.getByText('No data sets found').isVisible();
  }
}
