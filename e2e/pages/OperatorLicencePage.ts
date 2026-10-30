/**
 * Operator Licence page objects
 * Routes: /data/operators/licence/<number>  and  /data/operators/licence/<number>/line/details
 * (public URLs on the data host: /operators/licence/<number>/ and .../line/details/)
 * Django sources: transit_odp/browse/templates/browse/operators/licence_details.html and
 * transit_odp/browse/templates/browse/timetables/dataset_detail/licence_review_line_metadata.html
 */
import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class OperatorLicencePage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async navigate(licenceNumber: string): Promise<this> {
    return await this.navigateTo(`/data/operators/licence/${licenceNumber}`);
  }

  async verifyOnPage(licenceNumber?: string): Promise<this> {
    await expect(this.page).toHaveURL(new RegExp(`/operators/licence/${licenceNumber ?? '[^/]+'}/?(\\?.*)?$`));
    await expect(this.heading).toBeVisible();
    return this;
  }

  get heading() {
    return this.page.getByRole('heading', { level: 1 });
  }

  get breadcrumbs() {
    return this.page.getByRole('navigation', { name: 'Breadcrumb' });
  }

  get reviewServiceNumbersHeading() {
    return this.page.getByRole('heading', { level: 2, name: 'Review Service Numbers' });
  }

  get serviceLinks() {
    return this.page.locator('#licence-services-table tbody tr:not(.js-hidden) a');
  }

  checkbox(label: string) {
    return this.page.getByLabel(label, { exact: true });
  }

  sortHeader(name: string) {
    return this.page.getByRole('columnheader', { name });
  }

  async openFirstService(): Promise<OperatorLicenceLinePage> {
    await this.serviceLinks.first().click();
    return new OperatorLicenceLinePage(this.page);
  }
}

export class OperatorLicenceLinePage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async navigate(licenceNumber: string, query: string): Promise<this> {
    return await this.navigateTo(`/data/operators/licence/${licenceNumber}/line/details?${query}`);
  }

  async verifyOnPage(): Promise<this> {
    await expect(this.page).toHaveURL(/\/operators\/licence\/[^/]+\/line\/details\/?\?/);
    await expect(this.heading).toBeVisible();
    return this;
  }

  get heading() {
    return this.page.getByRole('heading', { level: 1 });
  }

  get breadcrumbs() {
    return this.page.getByRole('navigation', { name: 'Breadcrumb' });
  }

  get feedbackHeading() {
    return this.page.getByRole('heading', { level: 2, name: /^Noticed issues with this/ });
  }
}
