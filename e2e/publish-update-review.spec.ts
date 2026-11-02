import { Page } from '@playwright/test';
import { config } from './config';
import { test } from './fixtures';
import { PublishUpdateReviewPage } from './pages/PublishUpdateReviewPage';

// The review pages read everything from the review-status APIs, so stubbing them lets any dataset ID be used
// without running the publishing pipeline.
const DATASET_ID = '987654';

const json = (body: unknown) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });

async function stubProcessedRevision(page: Page): Promise<void> {
  await page.route('**/api/publish/dataset/*/progress/', (route) =>
    route.fulfill(json({ progress: 100, status: 'success' })),
  );
  await page.route('**/api/data/app/fare_stops/**', (route) =>
    route.fulfill(json({ type: 'FeatureCollection', features: [] })),
  );
}

test.describe('Publish update review journey', () => {
  test('Timetable update review - shows the update stepper and review heading', async ({ authenticatedPage }) => {
    const page = new PublishUpdateReviewPage(authenticatedPage);
    await stubProcessedRevision(authenticatedPage);
    await authenticatedPage.route('**/api/publish/timetables/data-quality-status/**', (route) =>
      route.fulfill(json('SUCCESS')),
    );
    await authenticatedPage.route('**/api/publish/timetables/review-status/**', (route) =>
      route.fulfill(
        json({
          datasetId: Number(DATASET_ID),
          revisionId: 1,
          status: 'success',
          progress: 100,
          loading: false,
          name: 'Playwright timetable update',
          description: 'Timetable description',
          shortDescription: 'Timetable',
          ownerName: config.testOrganisation.name,
          error: null,
          validationState: 'passed',
          metadata: [],
          dataQuality: { status: 'SUCCESS', criticalCount: 0, advisoryCount: 0, hasCriticalIssues: false },
        }),
      ),
    );

    await test.step('Open the timetable update review page', async () => {
      await page.navigateToReview('timetable', config.organisationId, DATASET_ID);
    });

    await test.step('Verify the update stepper and heading', async () => {
      await page.assertReviewLoaded('Playwright timetable update');
    });

    await test.step('Verify the Django property table, Edit targets and consent form', async () => {
      await page.assertTimetablePropertyTable(config.organisationId, DATASET_ID);
    });
  });

  test('Fares update review - matches the Django consent field and links', async ({ authenticatedPage }) => {
    const page = new PublishUpdateReviewPage(authenticatedPage);
    await stubProcessedRevision(authenticatedPage);
    await authenticatedPage.route('**/api/publish/fares/review-status/**', (route) =>
      route.fulfill(
        json({
          datasetId: Number(DATASET_ID),
          revisionId: 1,
          status: 'success',
          progress: 100,
          loading: false,
          name: 'Playwright fares update',
          description: 'Fares description',
          shortDescription: 'Fares',
          ownerName: config.testOrganisation.name,
          error: null,
          isFaresValidatorActive: false,
          validatorError: false,
          schemaError: false,
        }),
      ),
    );

    await test.step('Open the fares update review page', async () => {
      await page.navigateToReview('fares', config.organisationId, DATASET_ID);
    });

    await test.step('Verify the update stepper, consent checkbox and links', async () => {
      await page.assertReviewLoaded('Playwright fares update');
      await page.assertFaresConsentAndEditLinks(config.organisationId, DATASET_ID);
    });
  });

  for (const type of ['timetable', 'fares'] as const) {
    test(`${type} update review modify - reveals inputs and confirms cancel`, async ({ authenticatedPage }) => {
      const page = new PublishUpdateReviewPage(authenticatedPage);

      await test.step('Open the modify page with both inputs hidden', async () => {
        await page.navigateToModify(type, config.organisationId, DATASET_ID);
        await page.assertModifyForm();
      });

      await test.step('Reveal the URL and file inputs', async () => {
        await page.chooseUrl();
        await page.chooseFile();
      });

      await test.step('Cancel shows the confirmation step and Back returns to the form', async () => {
        await page.cancel();
        await page.assertCancelStep(type, config.organisationId, DATASET_ID);
        await page.backFromCancel();
        await page.assertModifyHeading();
      });
    });
  }
});
