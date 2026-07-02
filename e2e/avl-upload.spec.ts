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

  test('shows validation errors when upload fields are empty', async ({ authenticatedPage }) => {
    const page = new AvlUploadPage(authenticatedPage);

    await page.navigate(config.organisationId);
    await page.fillDescriptionStep('AVL validation test description', 'AVL validation');
    await page.continue();

    await page.assertUploadStep();
    await page.continue();

    await page.assertValidationSummary();
    await page.assertUploadErrorsVisible();
  });

  test('requires consent before enabling publish button', async ({ authenticatedPage }) => {
    const page = new AvlUploadPage(authenticatedPage);
    const runId = Date.now();

    await page.navigate(config.organisationId);
    await page.fillDescriptionStep(`Playwright AVL consent check ${runId}`, `AVL-${runId}`);
    await page.continue();

    await page.assertUploadStep();
    await page.fillUploadStep(config.avlFeed.url, config.testUser.username, config.testUser.password);
    await page.continue();

    await page.review.waitForReviewToBeReady();
    await page.review.assertPublishDisabled();
    await page.review.consentToPublish();
    await page.review.assertPublishEnabled();
  });

  test('cancel confirm returns user to AVL data feed list', async ({ authenticatedPage }) => {
    const page = new AvlUploadPage(authenticatedPage);

    await page.navigate(config.organisationId);
    await page.assertDescriptionStep();
    await page.clickCancel();
    await page.assertCancelModalVisible();
    await page.confirmCancelModal();
    await page.assertOnAvlListPage(config.organisationId);
  });

  test('maps backend create field errors onto upload step', async ({ authenticatedPage }) => {
    const page = new AvlUploadPage(authenticatedPage);

    await authenticatedPage.route('**/api/avl/create/**', async (route) => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          fieldErrors: {
            url_link: ['Enter a valid URL.'],
            username: ['Username is required.'],
            password: ['Password is required.'],
          },
        }),
      });
    });

    await page.navigate(config.organisationId);
    await page.fillDescriptionStep('AVL backend validation mapping', 'AVL backend');
    await page.continue();

    await page.assertUploadStep();
    await page.fillUploadStep('https://feed.example.com/avl', config.testUser.username, config.testUser.password);
    await page.continue();

    await page.assertValidationSummary();
    await page.assertUploadErrorsVisible();
  });

  test('shows review error state when processing returns failed upload', async ({ authenticatedPage }) => {
    const page = new AvlUploadPage(authenticatedPage);
    const orgId = config.organisationId;
    const fakeDatasetId = '999999';

    await authenticatedPage.route('**/api/avl/create/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          redirect: `/publish/org/${orgId}/dataset/avl/${fakeDatasetId}/review`,
        }),
      });
    });

    await authenticatedPage.route(`**/api/avl/review-status/${orgId}/${fakeDatasetId}/**`, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          datasetId: Number(fakeDatasetId),
          revisionId: 1,
          status: 'inactive',
          progress: 100,
          loading: false,
          error: 'Supplied feed could not be parsed.',
        }),
      });
    });

    await page.navigate(orgId);
    await page.fillDescriptionStep('AVL review failure path', 'AVL fail path');
    await page.continue();

    await page.assertUploadStep();
    await page.fillUploadStep('https://feed.example.com/avl', config.testUser.username, config.testUser.password);
    await page.continue();

    await page.review.waitForReviewToBeReady();
    await page.review.assertReviewError();
    await page.review.assertPublishCorrectFeedVisible();
  });
});