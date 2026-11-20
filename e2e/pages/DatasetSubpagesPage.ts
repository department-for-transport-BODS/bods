/**
 * Dataset sub-pages (changelog, subscription, feedback) on the data host.
 * Routes: /<timetable|avl|fares>/dataset/<id>/{changelog,subscription,feedback}
 */
import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export type DatasetKind = 'timetable' | 'avl' | 'fares';
export type DatasetSubpage = 'changelog' | 'subscription' | 'subscription/success' | 'feedback' | 'feedback/success';

export class DatasetSubpagesPage extends BasePage {
  constructor(
    page: Page,
    private readonly kind: DatasetKind,
    private readonly datasetId: string,
  ) {
    super(page);
  }

  path(subpage: DatasetSubpage): string {
    return `/${this.kind}/dataset/${this.datasetId}/${subpage}/`;
  }

  async open(subpage: DatasetSubpage): Promise<this> {
    return await this.navigateTo(this.path(subpage));
  }

  get heading() {
    return this.page.getByRole('heading', { level: 1 });
  }

  get backLink() {
    return this.page.getByRole('link', { name: 'Back', exact: true });
  }

  get changelogRows() {
    return this.page.locator('table.custom_govuk_table tbody tr');
  }

  get confirmButton() {
    return this.page.getByRole('button', { name: 'Confirm' });
  }

  get feedbackField() {
    return this.page.getByLabel('What best describes the issue you are experiencing?*');
  }

  get sendButton() {
    return this.page.getByRole('button', { name: 'Send' });
  }

  get errorSummary() {
    return this.page.locator('.govuk-error-summary');
  }

  async expectTitle(title: string | RegExp): Promise<this> {
    await expect(this.page).toHaveTitle(title);
    return this;
  }
}
