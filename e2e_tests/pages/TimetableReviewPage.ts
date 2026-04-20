/**
 * Timetable Review page object
 * Route: /publish/org/[orgId]/dataset/timetable/[datasetId]/review
 */
import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class TimetableReviewPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async navigate(orgId: string, datasetId: string): Promise<this> {
    return await this.navigateTo(`/publish/org/${orgId}/dataset/timetable/${datasetId}/review`);
  }

  async verifyOnPage(): Promise<this> {
    expect(this.page.url()).toContain('/review');
    return this;
  }

  async hasLoaded(): Promise<boolean> {
    await this.page.waitForLoadState('networkidle');
    return this.page.url().includes('/review');
  }

  async getHeading(): Promise<string | null> {
    return await this.page.locator('h1').textContent();
  }

  async isProcessing(): Promise<boolean> {
    const panel = this.page.locator('.govuk-panel');
    if (await panel.isVisible()) {
      const text = await panel.textContent();
      return text?.includes('processed') ?? false;
    }
    return false;
  }

  async getProgressPercentage(): Promise<string | null> {
    const body = this.page.locator('.govuk-panel__body');
    if (await body.isVisible()) {
      return await body.textContent();
    }
    return null;
  }

  async hasSummaryList(): Promise<boolean> {
    return await this.page.locator('.govuk-summary-list').isVisible();
  }

  async getSummaryValue(key: string): Promise<string | null> {
    const row = this.page.locator('.govuk-summary-list__row').filter({ hasText: key });
    const value = row.locator('.govuk-summary-list__value');
    if (await value.isVisible()) {
      return await value.textContent();
    }
    return null;
  }

  async hasDetectedServicesTable(): Promise<boolean> {
    return await this.page.locator('.govuk-table').isVisible();
  }

  async checkReviewedCheckbox(): Promise<this> {
    await this.page.locator('#id_has_reviewed').check();
    return this;
  }

  async isReviewedChecked(): Promise<boolean> {
    return await this.page.locator('#id_has_reviewed').isChecked();
  }

  async clickPublish(): Promise<this> {
    await this.page.getByRole('button', { name: /Publish/i }).click();
    return this;
  }

  async isPublishDisabled(): Promise<boolean> {
    return await this.page.getByRole('button', { name: /Publish/i }).isDisabled();
  }

  async clickBackToDataSets(): Promise<this> {
    await this.page.getByRole('link', { name: 'Back to data sets' }).click();
    return this;
  }

  async hasErrorSummary(): Promise<boolean> {
    return await this.page.locator('.govuk-error-summary').isVisible();
  }
}
