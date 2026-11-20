/**
 * Timetable feed detail page object
 * Route: /publish/org/[orgId]/dataset/timetable/[datasetId]
 * Django source: FeedDetailView (publish/dataset_detail/index.html)
 */
import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class TimetableFeedDetailPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async navigate(orgId: string, datasetId: string): Promise<this> {
    return await this.navigateTo(`/publish/org/${orgId}/dataset/timetable/${datasetId}`);
  }

  async verifyOnPage(): Promise<this> {
    await expect(this.page.getByText('Preview your service data status and make changes')).toBeVisible();
    return this;
  }

  async hasLoaded(): Promise<boolean> {
    await this.page.waitForLoadState('networkidle');
    return /\/dataset\/timetable\/\d+/.test(this.page.url());
  }

  propertyRow(label: string) {
    return this.page.locator('table tr', { has: this.page.getByRole('rowheader', { name: label }) });
  }

  async verifyPropertyRows(labels: string[]): Promise<this> {
    for (const label of labels) {
      await expect(this.propertyRow(label)).toBeVisible();
    }
    return this;
  }

  async verifyUpdateAndDeactivateActions(): Promise<this> {
    await expect(this.page.getByRole('link', { name: 'Update data set' })).toBeVisible();
    await expect(this.page.getByRole('link', { name: 'Deactivate data set' })).toBeVisible();
    return this;
  }

  async verifyHelpSidebar(): Promise<this> {
    await expect(this.page.getByRole('heading', { name: 'Need help with operator data requirements?' })).toBeVisible();
    return this;
  }

  async clickUpdateDataSet(): Promise<this> {
    await this.page.getByRole('link', { name: 'Update data set' }).click();
    return this;
  }
}
