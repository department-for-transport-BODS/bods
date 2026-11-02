import { Page } from '@playwright/test';
import { config } from './config';
import { test } from './fixtures';
import { PublishUpdateReviewPage } from './pages/PublishUpdateReviewPage';

// The review pages read everything from the review-status APIs, so stubbing them lets any dataset ID be used
// without running the publishing pipeline.
const DATASET_ID = '987654';

const json = (body: unknown) => ({ status: 200, contentType: 'application/json', body: JSON.stringify(body) });

const API_NAMESPACE = { timetable: 'timetables', fares: 'fares' } as const;

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
    for (const journey of ['update', 'publish'] as const) {
      const route = journey === 'update' ? 'update/review/update' : 'review/update';
      test(`${type} ${route} - reveals inputs and confirms cancel`, async ({ authenticatedPage }) => {
        const page = new PublishUpdateReviewPage(authenticatedPage);

        await test.step('Open the modify page with both inputs hidden', async () => {
          await page.navigateToModify(type, config.organisationId, DATASET_ID, journey);
          await page.assertModifyForm(journey);
        });

        await test.step('Reveal the URL and file inputs', async () => {
          await page.chooseUrl();
          await page.chooseFile();
        });

        await test.step('Cancel shows the confirmation step and Back returns to the form', async () => {
          await page.cancel();
          await page.assertCancelStep(type, config.organisationId, DATASET_ID, journey);
          await page.backFromCancel();
          await page.assertModifyHeading();
        });
      });
    }

    test(`${type} update - asks for a comment before the upload step`, async ({ authenticatedPage }) => {
      const page = new PublishUpdateReviewPage(authenticatedPage);
      await authenticatedPage.route(`**/api/publish/${API_NAMESPACE[type]}/update/**`, (route) =>
        route.request().method() === 'GET' ? route.fulfill(json({ urlLink: '' })) : route.abort(),
      );

      await test.step('Open the update page on the comment step', async () => {
        await page.navigateToUpdate(type, config.organisationId, DATASET_ID);
        await page.assertCommentStep();
      });

      await test.step('A missing comment shows the Django error', async () => {
        await page.continueWithoutComment();
      });

      await test.step('A comment moves on to the upload step', async () => {
        await page.continueWithComment('Playwright update comment');
      });
    });

    for (const journey of ['publish', 'update'] as const) {
      test(`${type} ${journey === 'update' ? 'update/success' : 'success'} - shows the Django confirmation panel`, async ({
        authenticatedPage,
      }) => {
        const page = new PublishUpdateReviewPage(authenticatedPage);
        await authenticatedPage.route(`**/api/publish/${API_NAMESPACE[type]}/update-success/**`, (route) =>
          route.fulfill(
            json({ isPtiCompliant: true, ptiEnforcedDate: '2021-08-02', isFaresValidatorActive: false, validatorError: false }),
          ),
        );

        await test.step('Open the success page', async () => {
          await page.navigateToSuccess(type, config.organisationId, DATASET_ID, journey);
        });

        await test.step('Verify the confirmation heading and title', async () => {
          await page.assertSuccessPanel(journey);
        });
      });
    }
  }
});
