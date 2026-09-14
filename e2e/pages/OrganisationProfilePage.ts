/**
 * Organisation Profile page object
 */
import { Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

export class OrganisationProfilePage extends BasePage {
  constructor(page: Page) {
    super(page);
  }

  /**
   * Navigate to organisation profile page by URL
   * @param orgId - Organisation ID (optional, if not provided navigates via UI)
   */
  async navigate(orgId?: number): Promise<this> {
    if (orgId !== undefined) {
      // Direct navigation to specific org ID
      return await this.navigateTo(`/account/manage/org-profile/${orgId}/`);
    } else {
      // Navigate via UI from dashboard
      return await this.navigateFromDashboard();
    }
  }

  /**
   * Navigate to organisation profile from dashboard using UI links
   * Follows: My account → Organisation profile
   */
  async navigateFromDashboard(): Promise<this> {
    // Click "My account" link
    await this.page.getByRole('link', { name: 'person-icon My account' }).click();
    await this.page.waitForLoadState('networkidle');

    // Click "Organisation profile" link
    await this.page.getByRole('link', { name: 'Organisation profile' }).click();
    await this.page.waitForLoadState('networkidle');

    return this;
  }

  /**
   * Verify we're on the organisation profile page
   */
  async verifyOnPage(): Promise<this> {
    expect(this.page.url()).toContain('/account/manage/org-profile/');
    return this;
  }

  /**
   * Check if page has loaded successfully
   */
  async hasLoaded(): Promise<boolean> {
    await this.page.waitForLoadState('networkidle');
    return this.page.url().includes('/account/manage/org-profile/');
  }

  /**
   * Get organisation name from the table next to "Short name" label
   */
  async getOrganisationName(): Promise<string | null> {
    const tableRow = this.page.locator('table thead tr').filter({ hasText: 'Short name' });
    const nameCell = tableRow.locator('th').nth(1);

    if (await nameCell.isVisible()) {
      return await nameCell.textContent();
    }
    return null;
  }
}
