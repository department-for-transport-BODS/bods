import { expect, Page } from '@playwright/test';

export class TimetableReviewSection {
  constructor(private readonly page: Page) {}

  async assertOnDataQualityReviewPage(orgId: string, timeoutMs = 180000): Promise<void> {
    await expect(this.page).toHaveURL(
      new RegExp(`/(?:publish/)?org/${orgId}/dataset/timetable/\\d+/review/?$`),
      { timeout: timeoutMs },
    );
    await expect(
      this.page.getByRole('heading', { name: /Validating data sets|Review and publish/ }).first(),
    ).toBeVisible();
  }
}