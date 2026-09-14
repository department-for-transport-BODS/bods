/**
 * Timetable Publish page object
 * Route: /publish/org/[orgId]/dataset/timetable
 * Multi-step form: 1. Describe data, 2. Provide data, 3. Review & publish
 */
import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class TimetablePublishPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async navigate(orgId: string): Promise<this> {
    return await this.navigateTo(`/publish/org/${orgId}/dataset/timetable`);
  }

  async verifyOnPage(): Promise<this> {
    expect(this.page.url()).toContain('/dataset/timetable');
    return this;
  }

  async hasLoaded(): Promise<boolean> {
    await this.page.waitForLoadState('networkidle');
    return this.page.url().includes('/dataset/timetable');
  }

  // --- Step 1: Describe your data set ---

  async verifyStep1Visible(): Promise<this> {
    await expect(this.page.locator('h1')).toContainText('Describe your data set');
    return this;
  }

  async fillDescription(description: string): Promise<this> {
    await this.page.locator('textarea, input').first().fill(description);
    return this;
  }

  async fillShortDescription(shortDescription: string): Promise<this> {
    await this.page.locator('textarea, input').nth(1).fill(shortDescription);
    return this;
  }

  async fillStep1(description: string, shortDescription: string): Promise<this> {
    await this.fillDescription(description);
    await this.fillShortDescription(shortDescription);
    return this;
  }

  async clickContinue(): Promise<this> {
    await this.page.getByRole('button', { name: 'Continue' }).click();
    return this;
  }

  // --- Step 2: Provide data ---

  async verifyStep2Visible(): Promise<this> {
    await expect(this.page.locator('h1')).toContainText('Choose how to provide your data set');
    return this;
  }

  async selectUrlLink(): Promise<this> {
    await this.page.locator('input[type="radio"]').first().check();
    return this;
  }

  async selectFileUpload(): Promise<this> {
    await this.page.locator('input[type="radio"]').nth(1).check();
    return this;
  }

  async fillUrlLink(url: string): Promise<this> {
    await this.page.locator('input[type="url"], input[type="text"]').last().fill(url);
    return this;
  }

  async uploadFile(filePath: string): Promise<this> {
    await this.page.locator('input[type="file"]').setInputFiles(filePath);
    return this;
  }

  // --- Step 3: Review and publish ---

  async verifyStep3Visible(): Promise<this> {
    await expect(this.page.locator('h1')).toContainText('Review and publish');
    return this;
  }

  async verifySummaryContains(text: string): Promise<this> {
    await expect(this.page.locator('.govuk-summary-list')).toContainText(text);
    return this;
  }

  async checkConsent(): Promise<this> {
    await this.page.locator('#id_consent').check();
    return this;
  }

  async isConsentChecked(): Promise<boolean> {
    return await this.page.locator('#id_consent').isChecked();
  }

  async clickPublish(): Promise<this> {
    await this.page.getByRole('button', { name: /Publish/i }).click();
    return this;
  }

  // --- Validation errors ---

  async hasErrorMessage(): Promise<boolean> {
    return await this.page.locator('.govuk-error-message').first().isVisible();
  }

  async getErrorMessages(): Promise<string[]> {
    const errors = this.page.locator('.govuk-error-message');
    const count = await errors.count();
    const messages: string[] = [];
    for (let i = 0; i < count; i++) {
      const text = await errors.nth(i).textContent();
      if (text) messages.push(text.trim());
    }
    return messages;
  }

  // --- Stepper ---

  async getStepperSteps(): Promise<string[]> {
    const steps = this.page.locator('[class*="stepper"], [class*="step"]').locator('li, span, div');
    const count = await steps.count();
    const labels: string[] = [];
    for (let i = 0; i < count; i++) {
      const text = await steps.nth(i).textContent();
      if (text?.trim()) labels.push(text.trim());
    }
    return labels;
  }
}
