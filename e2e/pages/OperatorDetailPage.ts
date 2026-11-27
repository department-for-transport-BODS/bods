/**
 * Operator Profile detail page object
 * Route: /data/operators/<id>  (public URL on the data host: /operators/<id>/)
 * Django source: transit_odp/browse/templates/browse/operators/operator_detail.html
 */
import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class OperatorDetailPage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  async navigate(operatorId: number | string): Promise<this> {
    return await this.navigateTo(`/data/operators/${operatorId}`);
  }

  async verifyOnPage(): Promise<this> {
    await expect(this.page).toHaveURL(/\/operators\/\d+\/?$/);
    await expect(this.page.getByRole('heading', { level: 1 })).toBeVisible();
    return this;
  }

  get heading() {
    return this.page.getByRole('heading', { level: 1 });
  }

  get breadcrumbs() {
    return this.page.getByRole('navigation', { name: 'Breadcrumb' });
  }

  get browseTimetablesLink() {
    return this.page.getByRole('link', { name: 'Browse Timetables data' });
  }

  get browseLocationLink() {
    return this.page.getByRole('link', { name: 'Browse Location data' });
  }

  get browseFaresLink() {
    return this.page.getByRole('link', { name: 'Browse Fares data' });
  }

  get registerLink() {
    return this.page.getByRole('link', { name: 'Register' });
  }

  get contactLink() {
    return this.page.getByRole('link', { name: /^Contact / });
  }
}
