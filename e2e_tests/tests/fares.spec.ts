import path from 'path';
import { test, expect } from './fixtures';
import { config } from '../config';

const FARES_SAMPLE_FILE = path.resolve(__dirname, '../../transit_odp/fares/tests/fixtures/sample.zip');

async function goToFaresCreateFromPublishData(authenticatedPage: any) {
  await authenticatedPage.goto(`${config.publishUrl}/publish`);
  await expect(authenticatedPage.getByRole('heading', { name: /publish bus open data/i })).toBeVisible();
  await authenticatedPage.getByRole('link', { name: /publish data/i }).click();
  await expect(authenticatedPage).toHaveURL(/\/publish\/org\/\d+\/dataset$/);
  await authenticatedPage.getByLabel('Fares').check();
  await authenticatedPage.getByRole('button', { name: 'Continue' }).click();
  await expect(authenticatedPage).toHaveURL(/\/publish\/org\/\d+\/dataset\/fares\/create$/);
}

async function goToFaresList(authenticatedPage: any) {
  await authenticatedPage.goto(`${config.publishUrl}/publish`);
  await authenticatedPage.getByRole('link', { name: /review my data/i }).click();

  // route to an intermediate dataset page or back to the
  const currentUrl = authenticatedPage.url();
  const orgMatch = currentUrl.match(/\/publish\/org\/(\d+)/);
  if (orgMatch && !/\/dataset\/fares(\?|$)/.test(currentUrl)) {
    await authenticatedPage.goto(`${config.publishUrl}/publish/org/${orgMatch[1]}/dataset/fares`);
  }

  await expect(authenticatedPage).toHaveURL(/\/publish\/org\/\d+\/dataset\/fares(\?tab=active)?$/);
}

async function clickFirstDatasetLinkOrSkip(authenticatedPage: any, reason: string) {
  // post-navigation settle time, then check for either rows or empty state.
  await authenticatedPage.waitForLoadState('domcontentloaded', { timeout: 5000 }).catch(() => {});

  const loading = authenticatedPage.getByText('Loading data sets...').first();
  await loading.waitFor({ state: 'hidden', timeout: 5000 }).catch(() => {});

  const firstDatasetLink = authenticatedPage.locator('table.custom_govuk_table tbody tr td:nth-child(2) a').first();
  const emptyState = authenticatedPage.getByText('No data sets found').first();

  await expect
    .poll(
      async () => (await firstDatasetLink.count()) > 0 || (await emptyState.isVisible()),
      { timeout: 5000 },
    )
    .toBe(true);

  if ((await firstDatasetLink.count()) === 0) {
    test.skip(true, reason);
  }
  await firstDatasetLink.click();
}

test.describe('Fares pages', () => {
  test('can open fares list from publish dashboard', async ({ authenticatedPage }) => {
    await goToFaresList(authenticatedPage);
    await expect(authenticatedPage).toHaveURL(/\/publish(\/org\/\d+\/dataset\/fares)?(\?tab=active)?$/);
    await expect(authenticatedPage.getByRole('link', { name: /publish new data feeds/i })).toBeVisible({ timeout: 60000 });
  });

  test('supports fares tab navigation', async ({ authenticatedPage }) => {
    await goToFaresList(authenticatedPage);

    await authenticatedPage.getByRole('link', { name: 'Draft' }).click();
    await expect(authenticatedPage).toHaveURL(/\?tab=draft$/);

    await authenticatedPage.getByRole('link', { name: 'Inactive' }).click();
    await expect(authenticatedPage).toHaveURL(/\?tab=archive$/);
  });

  test('Fares form 3 step flow', async ({ authenticatedPage }) => {
    await goToFaresCreateFromPublishData(authenticatedPage);

    await expect(authenticatedPage.getByRole('heading', { name: 'Describe your data set' })).toBeVisible();
    await authenticatedPage.getByRole('button', { name: 'Continue' }).click();

    await expect(authenticatedPage.getByText('There is a problem')).toBeVisible();
    await expect(
      authenticatedPage.getByText('Enter a data set description and short description.'),
    ).toBeVisible();

    await authenticatedPage.fill('#id_description-description', 'Playwright fares dataset description');
    await authenticatedPage.fill('#id_description-short_description', 'Fares smoke test');
    await authenticatedPage.getByRole('button', { name: 'Continue' }).click();

    await expect(
      authenticatedPage.getByRole('heading', { name: 'Choose how to provide your data set' }),
    ).toBeVisible();

    await authenticatedPage.getByLabel('Upload data set to Bus Open Data Service').check();
    await authenticatedPage.locator('#id_upload_file').setInputFiles(FARES_SAMPLE_FILE);
    await authenticatedPage.getByRole('button', { name: 'Continue' }).click();

    await expect(authenticatedPage).toHaveURL(/\/publish\/org\/\d+\/dataset\/fares\/\d+\/review$/);
  });

  test('draft tab dataset links open review page', async ({ authenticatedPage }) => {
    await goToFaresList(authenticatedPage);
    await authenticatedPage.getByRole('link', { name: 'Draft' }).click();
    await expect(authenticatedPage).toHaveURL(/\?tab=draft$/);

    await clickFirstDatasetLinkOrSkip(
      authenticatedPage,
      'No draft fares datasets are available in this environment.',
    );

    await expect(authenticatedPage).toHaveURL(/\/publish\/org\/\d+\/dataset\/fares\/\d+\/review$/);

    const processingHeading = authenticatedPage.getByRole('heading', { name: /your data is being processed/i });
    const reviewCheckboxText = authenticatedPage.getByText('I have reviewed the submission and wish to publish my data');

    // Draft review page can be in either state:
    // 1) processing in progress, or 2) ready for review/publish actions.
    await expect
      .poll(
        async () => (await processingHeading.isVisible()) || (await reviewCheckboxText.isVisible()),
        { timeout: 60000 },
      )
      .toBe(true);

    if (await reviewCheckboxText.isVisible()) {
      await expect(authenticatedPage.getByRole('button', { name: 'Publish data' })).toBeVisible();
      await expect(authenticatedPage.getByRole('link', { name: 'Delete data set' })).toBeVisible();
    }
  });

  test('inactive tab dataset links open detail page', async ({ authenticatedPage }) => {
    await goToFaresList(authenticatedPage);
    await authenticatedPage.getByRole('link', { name: 'Inactive' }).click();
    await expect(authenticatedPage).toHaveURL(/\?tab=archive$/);

    await clickFirstDatasetLinkOrSkip(
      authenticatedPage,
      'No inactive fares datasets are available in this environment.',
    );

    await expect(authenticatedPage).toHaveURL(/\/publish\/org\/\d+\/dataset\/fares\/\d+$/);
    await expect(authenticatedPage.getByRole('heading', { level: 1 })).toBeVisible();
  });

});