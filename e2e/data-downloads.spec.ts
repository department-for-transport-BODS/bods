import { expect, test } from '@playwright/test';
import { DataDownloadsPage, dataUrl } from './pages/DataDownloadsPage';

test.describe('Data host - downloads, catalogue and 404 handling', () => {
  test('Downloads page lists every dataset download with its Django link', async ({ page }) => {
    const downloads = new DataDownloadsPage(page);

    await test.step('Open /downloads/', async () => {
      await downloads.open();
    });

    await test.step('Each dataset type links to its download page', async () => {
      await downloads.verifyDownloadLinks();
    });
  });

  test('Downloads page help modal opens and closes', async ({ page }) => {
    const downloads = new DataDownloadsPage(page);
    await downloads.open();

    await downloads.openHelpModal('TransXChange');
    const modal = page.locator('.help-modal .overlay.active');
    await expect(modal.getByRole('heading', { name: 'TransXChange' })).toBeVisible();

    await modal.getByRole('button', { name: 'Close' }).click();
    await expect(modal).toHaveCount(0);
  });

  test('Data catalogue responds with a file download or redirect, never the app shell', async ({
    request,
  }) => {
    const response = await request.get(dataUrl('/catalogue/'), { maxRedirects: 0 });

    expect([200, 302, 404]).toContain(response.status());
    if (response.status() === 200) {
      expect(response.headers()['content-disposition']).toContain('attachment');
    }
  });

  for (const unknownPath of ['/foo', '/downloads-does-not-exist', '/999999999']) {
    test(`Unknown data path ${unknownPath} shows the site 404 page with a 404 status`, async ({
      page,
    }) => {
      const downloads = new DataDownloadsPage(page);

      const status = await downloads.openUnknownPath(unknownPath);

      expect(status).toBe(404);
      await expect(downloads.notFoundHeading).toBeVisible();
      await expect(page.getByText('If you typed the web address, check it is correct.')).toBeVisible();
    });
  }
});
