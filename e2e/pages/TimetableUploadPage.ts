import { expect, Page } from '@playwright/test';
import { TimetableReviewSection } from '../components/TimetableReviewSection';

export class TimetableUploadPage {
  readonly review: TimetableReviewSection;

  constructor(private readonly page: Page) {
    this.review = new TimetableReviewSection(page);
  }

  async navigate(orgId: string): Promise<void> {
    await this.page.goto(`/publish/org/${orgId}/dataset/timetable/new`, { waitUntil: 'domcontentloaded' });
  }

  async assertDescriptionStep(): Promise<void> {
    await expect(this.page.getByRole('heading', { name: 'Describe your data set' })).toBeVisible();
  }

  async fillDescriptionStep(description: string, shortDescription: string): Promise<void> {
    await this.page.locator('#id_description').fill(description);
    await this.page.locator('#id_short_description').fill(shortDescription);
  }

  async continue(): Promise<void> {
    await this.page.getByRole('button', { name: 'Continue' }).click();
  }

  async assertUploadStep(): Promise<void> {
    await expect(this.page.getByRole('heading', { name: 'Choose how to provide your data set' })).toBeVisible();
  }

  async provideDataByUrl(url: string): Promise<void> {
    await this.page.locator('#method-link').check();
    await this.page.locator('#id_url_link').fill(url);
  }

  async assertUploadError(message: string): Promise<void> {
    await expect(this.page.locator('.govuk-error-message')).toContainText(message);
    await this.assertUploadStep();
  }
}