import { config } from './config';
import { test } from './fixtures';
import { AvlUploadPage } from './pages/AvlUploadPage';

test.describe('AVL upload migration flow', () => {
  test('can upload an AVL feed and publish it', async ({ authenticatedPage }) => {
    test.slow();

    const page = new AvlUploadPage(authenticatedPage);
    const runId = Date.now();

    await page.navigate(config.organisationId);
    await page.assertDescriptionStep();
    await page.fillDescriptionStep(`Playwright AVL upload ${runId}`, `AVL-${runId}`);
    await page.continue();

    await page.assertUploadStep();
    await page.fillUploadStep(
      config.avlFeed.url,
      config.testUser.username,
      config.testUser.password,
    );
    await page.continue();

    await page.review.waitForReviewToBeReady();
    await page.review.consentToPublish();
    await page.review.publish();

    await page.assertSuccess();
  });

  test('shows validation errors when description fields are empty', async ({ authenticatedPage }) => {
    const page = new AvlUploadPage(authenticatedPage);

    await page.navigate(config.organisationId);
    await page.assertDescriptionStep();
    await page.continue();

    await page.assertValidationSummary();
    await page.assertDescriptionErrorsVisible();
  });
});