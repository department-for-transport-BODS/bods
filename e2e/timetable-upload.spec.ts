import { config } from './config';
import { test } from './fixtures';
import { TimetableUploadPage } from './pages/TimetableUploadPage';

test.describe('Timetable upload migration flow', () => {
  test('shows an error when the timetable URL cannot be uploaded', async ({ authenticatedPage }) => {
    const page = new TimetableUploadPage(authenticatedPage);
    const errorMessage = 'Unable to download a timetable from this URL.';

    await authenticatedPage.route('**/api/publish/timetables/create/**', async (route) => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ detail: errorMessage }),
      });
    });

    await page.navigate(config.organisationId);
    await page.assertDescriptionStep();
    await page.fillDescriptionStep('Playwright invalid timetable URL', 'Invalid timetable URL');
    await page.continue();

    await page.assertUploadStep();
    await page.provideDataByUrl('https://invalid.example/timetable.xml');
    await page.continue();

    await page.assertUploadError(errorMessage);
  });

  test('reaches the data quality review page after uploading a timetable URL', async ({ authenticatedPage }) => {
    test.slow();

    const page = new TimetableUploadPage(authenticatedPage);
    const runId = Date.now();

    await page.navigate(config.organisationId);
    await page.assertDescriptionStep();
    await page.fillDescriptionStep(`Playwright timetable upload ${runId}`, `Timetable ${runId}`.slice(0, 30));
    await page.continue();

    await page.assertUploadStep();
    await page.provideDataByUrl(config.timetableFeed.url);
    await page.continue();

    await page.review.assertOnDataQualityReviewPage(config.organisationId);
  });
});