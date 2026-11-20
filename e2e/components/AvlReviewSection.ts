import { expect, Page } from '@playwright/test';

export class AvlReviewSection {
  constructor(private readonly page: Page) {}

  private publishButton() {
    return this.page.getByRole('button', { name: /publish data|publish data feed|publishing/i });
  }

  async waitForReviewToBeReady(timeoutMs = 180000): Promise<void> {
    await expect(this.page.getByRole('heading', { name: 'Review and publish' })).toBeVisible();

    const reviewSection = this.page.locator('#preview-section');
    if (await reviewSection.isVisible()) {
      return;
    }

    await reviewSection.waitFor({ state: 'visible', timeout: timeoutMs });
  }

  async consentToPublish(): Promise<void> {
    await this.page.locator('#id_has_reviewed').check();
    await expect(this.page.locator('#id_has_reviewed')).toBeChecked();
  }

  async publish(): Promise<void> {
    await this.publishButton().click();
  }

  async assertPublishDisabled(): Promise<void> {
    await expect(this.publishButton()).toBeDisabled();
  }

  async assertPublishEnabled(): Promise<void> {
    await expect(this.publishButton()).toBeEnabled();
  }

  async assertReviewError(): Promise<void> {
    await expect(this.page.getByText('Supplied data feed has failed to upload')).toBeVisible();
  }

  async assertPublishCorrectFeedVisible(): Promise<void> {
    await expect(this.page.getByRole('button', { name: 'Publish correct data feed' })).toBeVisible();
  }
}