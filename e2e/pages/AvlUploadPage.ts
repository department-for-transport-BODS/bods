import { expect, Page } from '@playwright/test';
import { AvlReviewSection } from '../components/AvlReviewSection';

export class AvlUploadPage {
  readonly review: AvlReviewSection;

  constructor(private readonly page: Page) {
    this.review = new AvlReviewSection(page);
  }

  async navigate(orgId: string): Promise<void> {
    await this.page.goto(`/publish/org/${orgId}/dataset/avl/new`, { waitUntil: 'domcontentloaded' });
  }

  async assertDescriptionStep(): Promise<void> {
    await expect(this.page.getByRole('heading', { name: 'Describe your data feed' })).toBeVisible();
  }

  async fillDescriptionStep(description: string, shortDescription: string): Promise<void> {
    await this.page.locator('#id_description').fill(description);
    await this.page.locator('#id_short_description').fill(shortDescription);
  }

  async continue(): Promise<void> {
    await this.page.getByRole('button', { name: 'Continue' }).first().click();
  }

  async clickCancel(): Promise<void> {
    await this.page.getByRole('button', { name: 'Cancel' }).first().click();
  }

  async assertCancelModalVisible(): Promise<void> {
    await expect(this.page.getByText('Would you like to cancel publishing this data feed?')).toBeVisible();
  }

  async confirmCancelModal(): Promise<void> {
    await this.page.getByRole('button', { name: 'Confirm' }).click();
  }

  async assertOnAvlListPage(orgId: string): Promise<void> {
    await expect(this.page).toHaveURL(new RegExp(`/publish/org/${orgId}/dataset/avl/?$`));
  }

  async assertUploadStep(): Promise<void> {
    await expect(this.page.getByRole('heading', { name: 'Provide your data using the link below' })).toBeVisible();
  }

  async fillUploadStep(url: string, username: string, password: string): Promise<void> {
    await this.page.locator('#id_url_link').fill(url);
    await this.page.locator('#id_username').fill(username);
    await this.page.locator('#id_password').fill(password);
  }

  async assertValidationSummary(): Promise<void> {
    await expect(this.page.getByRole('heading', { name: 'There is a problem' })).toBeVisible();
  }

  async assertDescriptionErrorsVisible(): Promise<void> {
    await expect(this.page.locator('.govuk-error-summary a[href="#id_description"]')).toBeVisible();
    await expect(this.page.locator('.govuk-error-summary a[href="#id_short_description"]')).toBeVisible();
  }

  async assertUploadErrorsVisible(): Promise<void> {
    await expect(this.page.locator('.govuk-error-summary a[href="#id_url_link"]')).toBeVisible();
    await expect(this.page.locator('.govuk-error-summary a[href="#id_username"]')).toBeVisible();
    await expect(this.page.locator('.govuk-error-summary a[href="#id_password"]')).toBeVisible();
  }

  async assertSuccess(): Promise<void> {
    await expect(this.page.getByText('Your data feed has been successfully published')).toBeVisible();
  }
}