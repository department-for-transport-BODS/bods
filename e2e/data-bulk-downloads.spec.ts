import { test, expect } from './fixtures';
import { DataBulkDownloadPage, BulkDownloadKind } from './pages/DataBulkDownloadPage';

const LOGIN_REQUIRED: BulkDownloadKind[] = ['timetable', 'avl', 'fares', 'disruptions'];

test.describe('Data host - bulk download pages', () => {
  for (const kind of LOGIN_REQUIRED) {
    test(`/${kind}/download redirects anonymous users to login`, async ({ page }) => {
      const downloadPage = new DataBulkDownloadPage(page, kind);

      await downloadPage.open();

      await downloadPage.verifyRedirectedToLogin();
    });
  }

  test('Coach download page is public', async ({ page }) => {
    const downloadPage = new DataBulkDownloadPage(page, 'coach');

    await downloadPage.open();

    await downloadPage.verifyLoaded();
  });
});

test.describe('Data host - bulk download pages (signed in)', () => {
  for (const kind of LOGIN_REQUIRED) {
    test(`/${kind}/download renders for a signed-in user`, async ({ authenticatedPage }) => {
      const downloadPage = new DataBulkDownloadPage(authenticatedPage, kind);

      await test.step('Open the page', async () => {
        await downloadPage.open();
      });

      await test.step('Heading and help links are shown', async () => {
        await downloadPage.verifyLoaded();
      });
    });
  }

  test('AVL download help modal opens and closes', async ({ authenticatedPage }) => {
    const downloadPage = new DataBulkDownloadPage(authenticatedPage, 'avl');
    await downloadPage.open();
    await downloadPage.verifyLoaded();

    await downloadPage.openHelpModal('SIRI-VM');
    const modal = authenticatedPage.locator('.help-modal .overlay.active');
    await expect(modal.getByRole('heading', { name: 'SIRI-VM' })).toBeVisible();

    await modal.getByRole('button', { name: 'Close' }).click();
    await expect(modal).toHaveCount(0);
  });
});
