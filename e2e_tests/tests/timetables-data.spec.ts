import { test, expect } from '@playwright/test';
import { config } from '../config';
import { TimetablesDataPage } from '../pages/TimetablesDataPage';

test.describe('Timetables Data Page (Unauthenticated)', () => {

  test('timetables data page loads successfully', async ({ page }) => {
    const timetablesPage = new TimetablesDataPage(page);
    await timetablesPage.navigate();
    await timetablesPage.verifyOnPage();
    expect(await timetablesPage.hasLoaded()).toBe(true);
  });

  test('timetables data page has correct heading', async ({ page }) => {
    const timetablesPage = new TimetablesDataPage(page);
    await timetablesPage.navigate();
    const heading = await timetablesPage.getHeading();
    expect(heading).toContain('Timetables data');
  });

  test('timetables data page has main content area', async ({ page }) => {
    const timetablesPage = new TimetablesDataPage(page);
    await timetablesPage.navigate();
    expect(await timetablesPage.hasMainContent()).toBe(true);
  });

  test('timetables data page has search input', async ({ page }) => {
    const timetablesPage = new TimetablesDataPage(page);
    await timetablesPage.navigate();
    expect(await timetablesPage.hasSearchInput()).toBe(true);
  });

  test('timetables data page can accept search input', async ({ page }) => {
    const timetablesPage = new TimetablesDataPage(page);
    await timetablesPage.navigate();
    await timetablesPage.searchFor('Test Operator');
    // Verify the search input accepted the text without error
    const searchInput = page.locator('input[type="search"], input[type="text"]').first();
    await expect(searchInput).toHaveValue('Test Operator');
  });

  test('timetables data page is navigable from data page', async ({ page }) => {
    await page.goto(`${config.baseUrl}/data`);
    await page.waitForLoadState('networkidle');
    const timetablesLink = page.getByRole('link', { name: /Timetables data/i });
    await expect(timetablesLink).toBeVisible();
    await timetablesLink.click();
    await page.waitForLoadState('networkidle');
    expect(page.url()).toContain('/data/timetables');
  });
});
