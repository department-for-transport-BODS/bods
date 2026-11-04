import { test, expect } from '@playwright/test';
import { config } from './config';
import { LocalAuthorityPage } from './pages/LocalAuthorityPage';

test.describe('Local Transport Authority pages (Unauthenticated)', () => {
  test('list page loads with the Django heading, breadcrumb and search', async ({ page }) => {
    const lta = new LocalAuthorityPage(page);
    await lta.navigate();
    await lta.verifyOnListPage();
    await expect(page.getByText('Search for a specific Local Transport Authority')).toBeVisible();
    await expect(lta.searchInput).toBeVisible();
    await expect(lta.sortSelect).toHaveValue('ui_lta_name_trimmed');
  });

  test('searching keeps the term in the URL and the pill', async ({ page }) => {
    const lta = new LocalAuthorityPage(page);
    await lta.navigate();
    await lta.search('zzzz-no-such-authority');
    await expect(page).toHaveURL(/[?&]q=zzzz-no-such-authority/);
    await expect(page.getByRole('heading', { name: /Sorry, no results found for zzzz-no-such-authority/ })).toBeVisible();
    await expect(page.getByText('Check your spelling and try again')).toBeVisible();
  });

  test('an authority can be opened from the list when data exists', async ({ page }) => {
    const lta = new LocalAuthorityPage(page);
    await lta.navigate();
    await page.waitForLoadState('networkidle');
    test.skip((await lta.resultLinks.count()) === 0, 'No local transport authorities in this environment');

    await lta.openFirstAuthority();
    await expect(page).toHaveURL(/\/local-authority\/detail\?auth_ids=/);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    await expect(page.getByText('Need further help?')).toBeVisible();
  });

  test('detail page shows the Next.js 404 for an unknown authority', async ({ page }) => {
    await page.goto(`${config.baseUrl}/data/local-authority/detail?auth_ids=999999999`);
    await expect(page.getByRole('heading', { name: /not found/i })).toBeVisible();
  });

  test('export downloads reject a missing auth_ids', async ({ request }) => {
    const response = await request.get(`${config.baseUrl}/data/local-authority/export`, { maxRedirects: 5 });
    expect(response.status()).toBe(404);
  });
});
