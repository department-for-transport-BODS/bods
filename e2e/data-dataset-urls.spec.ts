import { test, expect } from '@playwright/test';
import { BrowseDatasetType, DatasetBrowsePage } from './pages/DatasetBrowsePage';

test.describe('Data host - dataset browsing URLs match Django', () => {
  for (const type of ['timetable', 'avl', 'fares'] as BrowseDatasetType[]) {
    test(`List page loads at /${type}`, async ({ page }) => {
      const browse = new DatasetBrowsePage(page);
      await browse.openList(type);
      await browse.expectOnList(type);
    });
  }

  test('Timetable list keeps its query parameters', async ({ page }) => {
    const browse = new DatasetBrowsePage(page);
    await browse.openList('timetable', '?status=live');
    await expect(page).toHaveURL(/\/timetable\?status=live$/);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });

  test('Search page links to the Django list URLs', async ({ page }) => {
    const browse = new DatasetBrowsePage(page);
    await browse.openSearch();
    for (const type of ['timetable', 'avl', 'fares'] as BrowseDatasetType[]) {
      await expect(page.locator(`main a[href$="/${type}?status=live"]`)).toHaveCount(1);
    }
  });

  test('A dataset on the timetable list opens at /timetable/dataset/<id>', async ({ page }) => {
    const browse = new DatasetBrowsePage(page);
    await browse.openList('timetable', '?status=live');
    const links = browse.datasetLinks('timetable');
    await page.waitForLoadState('networkidle');
    test.skip((await links.count()) === 0, 'No live timetable datasets in this environment');
    const href = await links.first().getAttribute('href');
    expect(href).toMatch(/\/timetable\/dataset\/\d+$/);
    await links.first().click();
    await expect(page).toHaveURL(/\/timetable\/dataset\/\d+$/);
  });

  for (const oldPath of ['/timetables', '/timetables?status=live', '/60', '/999999999']) {
    test(`Non-Django path ${oldPath} shows the site 404 page with a 404 status`, async ({ page }) => {
      const browse = new DatasetBrowsePage(page);
      const status = await browse.openPath(oldPath);
      expect(status).toBe(404);
      await expect(browse.notFoundHeading).toBeVisible();
    });
  }

  test('Unknown timetable dataset id shows the site 404 page', async ({ page }) => {
    const browse = new DatasetBrowsePage(page);
    const status = await browse.openPath('/timetable/dataset/999999999');
    expect(status).toBe(404);
    await expect(browse.notFoundHeading).toBeVisible();
  });
});
