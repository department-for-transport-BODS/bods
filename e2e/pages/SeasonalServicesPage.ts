/**
 * Seasonal services page object
 * Routes (publish host):
 *   /publish/org/[orgId]/dataset/timetable/seasonal-service
 *   /publish/org/[orgId]/dataset/timetable/seasonal-service/add-new
 *   /publish/org/[orgId]/dataset/timetable/seasonal-service/[serviceId]/edit-date
 */
import { Locator, Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class SeasonalServicesPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async navigate(orgId: string, query = ''): Promise<this> {
    return await this.navigateTo(`/publish/org/${orgId}/dataset/timetable/seasonal-service${query}`);
  }

  async navigateToAddNew(orgId: string): Promise<this> {
    return await this.navigateTo(`/publish/org/${orgId}/dataset/timetable/seasonal-service/add-new`);
  }

  async verifyOnList(): Promise<this> {
    await expect(this.page.getByRole('heading', { level: 1, name: 'Seasonal service operating dates' })).toBeVisible();
    await expect(this.page.getByRole('button', { name: 'Add new date range' })).toBeVisible();
    return this;
  }

  // --- List ---

  /** The table row whose "Service code" cell is `<licence>/<code>`. */
  rowForServiceCode(serviceCode: string): Locator {
    return this.page.getByRole('row').filter({ has: this.page.getByRole('cell', { name: serviceCode, exact: true }) });
  }

  async sortBy(column: string): Promise<this> {
    await this.page.getByRole('button', { name: new RegExp(`^${column}`) }).click();
    return this;
  }

  async clickAddNew(): Promise<this> {
    await this.page.getByRole('button', { name: 'Add new date range' }).click();
    return this;
  }

  async clickEditDates(serviceCode: string): Promise<this> {
    await this.rowForServiceCode(serviceCode).getByRole('link', { name: 'Edit dates' }).click();
    return this;
  }

  async clickDelete(serviceCode: string): Promise<this> {
    await this.rowForServiceCode(serviceCode).getByRole('button', { name: 'Delete' }).click();
    return this;
  }

  // --- Wizard / edit forms ---

  async selectLicence(licenceNumber: string): Promise<this> {
    await this.page.getByLabel('PSV licence number').selectOption({ label: licenceNumber });
    return this;
  }

  async firstLicenceNumber(): Promise<string> {
    const option = this.page.locator('#id_select_psv_licence_number-licence option').nth(1);
    return (await option.textContent())?.trim() ?? '';
  }

  async fillServiceCode(code: string): Promise<this> {
    await this.page.getByLabel('Service code').fill(code);
    return this;
  }

  async fillDates(start: string, end: string): Promise<this> {
    await this.page.getByLabel('Service begins on').fill(start);
    await this.page.getByLabel('Service ends on').fill(end);
    return this;
  }

  async clickContinue(): Promise<this> {
    await this.page.getByRole('button', { name: 'Continue' }).click();
    return this;
  }

  async clickSave(): Promise<this> {
    await this.page.getByRole('button', { name: 'Save' }).click();
    return this;
  }

  async clickCancel(): Promise<this> {
    await this.page.getByRole('link', { name: 'Cancel' }).click();
    return this;
  }

  async verifyStep2Visible(): Promise<this> {
    await expect(this.page.getByText('2. Provide operating dates')).toBeVisible();
    await expect(this.page.getByLabel('Service code')).toBeVisible();
    return this;
  }

  errorSummary(): Locator {
    return this.page.locator('.govuk-error-summary');
  }

  async errorSummaryMessages(): Promise<string[]> {
    return await this.errorSummary().locator('li').allTextContents();
  }
}
