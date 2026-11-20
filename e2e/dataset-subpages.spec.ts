import { test, expect } from './fixtures';
import { DatasetSubpagesPage } from './pages/DatasetSubpagesPage';

// A live timetable dataset on the target environment.
const DATASET_ID = process.env.E2E_TIMETABLE_DATASET_ID ?? '1';

test.describe('Dataset sub-pages (unauthenticated)', () => {
  test('Changelog - shows the revision table and a back link to the dataset', async ({ page }) => {
    const subpages = new DatasetSubpagesPage(page, 'timetable', DATASET_ID);
    await subpages.open('changelog');

    await subpages.expectTitle('Changelog');
    await expect(page.getByText('Changelog', { exact: true }).first()).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Comment' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Status' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Updated date' })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: 'Data quality' })).toBeVisible();
    await expect(subpages.changelogRows.first()).toBeVisible();
    await expect(subpages.backLink).toHaveAttribute('href', new RegExp(`/timetable/dataset/${DATASET_ID}/?$`));
  });

  test('Changelog - an unknown dataset is a 404', async ({ page }) => {
    const subpages = new DatasetSubpagesPage(page, 'timetable', '999999999');
    await subpages.open('changelog');

    await expect(page.getByRole('heading', { name: /page not found/i })).toBeVisible();
  });

  test('Subscription - anonymous visitors are asked to sign in', async ({ page }) => {
    const subpages = new DatasetSubpagesPage(page, 'timetable', DATASET_ID);
    await subpages.open('subscription');

    await expect(page.getByRole('heading', { name: 'Get data set updates' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign in' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Create account' })).toBeVisible();
  });

  test('Feedback - anonymous visitors are sent to sign in', async ({ page }) => {
    const subpages = new DatasetSubpagesPage(page, 'timetable', DATASET_ID);
    await subpages.open('feedback');

    await expect(page).toHaveURL(/login/);
  });
});

// The authenticatedPage fixture reuses the login saved by global-setup.
test.describe('Dataset sub-pages (signed in)', () => {
  test('Feedback - an empty form shows the Django validation message', async ({ authenticatedPage: page }) => {
    const subpages = new DatasetSubpagesPage(page, 'timetable', DATASET_ID);
    await subpages.open('feedback');

    await expect(page.getByRole('heading', { name: 'Contact the data set owner' })).toBeVisible();
    await subpages.sendButton.click();

    await expect(subpages.errorSummary).toBeVisible();
    await subpages.expectTitle('Error: Provide feedback');
  });

  test('Subscription - the confirmation page offers Confirm and Cancel', async ({ authenticatedPage: page }) => {
    const subpages = new DatasetSubpagesPage(page, 'timetable', DATASET_ID);
    await subpages.open('subscription');

    await expect(subpages.heading).toHaveText(/(Subscribe to|Unsubscribe from) data set/);
    await expect(subpages.confirmButton).toBeVisible();
    await expect(page.getByRole('link', { name: 'Cancel' })).toBeVisible();
  });
});
