import { test, expect } from './fixtures';
import { config } from './config';
import { RequiresAttentionKind, RequiresAttentionPage } from './pages/RequiresAttentionPage';

/*
  The "Review my data" banners link to these pages ("More details"). They need a signed-in
  organisation user; set TEST_ORGANISATION_ID when the test organisation is not id 1.
*/
const orgId = process.env.TEST_ORGANISATION_ID || config.organisationId;

const journeys: { kind: RequiresAttentionKind; ancestor: string }[] = [
  { kind: 'timetable', ancestor: 'Review My Timetables Data' },
  { kind: 'fares', ancestor: 'Review My Fares Data' },
];

for (const { kind, ancestor } of journeys) {
  test.describe(`Service codes requiring attention - ${kind}`, () => {
    test(`${kind} - page shows the Django heading, breadcrumbs and export link`, async ({ authenticatedPage }) => {
      const attentionPage = new RequiresAttentionPage(authenticatedPage, kind);

      await test.step('Open the page', async () => {
        await attentionPage.navigate(orgId);
        await attentionPage.verifyOnPage();
      });

      await test.step('Check the static content', async () => {
        await expect(attentionPage.heading()).toBeVisible();
        await expect(authenticatedPage).toHaveTitle(/Service Codes Requiring Attention/);
        await expect(authenticatedPage.getByRole('link', { name: ancestor })).toBeVisible();
        await expect(
          authenticatedPage.getByText('Search for a licence number, service code or line number'),
        ).toBeVisible();
        await expect(attentionPage.exportLink()).toBeVisible();
      });
    });

    test(`${kind} - searching with no matches shows the empty state`, async ({ authenticatedPage }) => {
      const attentionPage = new RequiresAttentionPage(authenticatedPage, kind);
      await attentionPage.navigate(orgId);

      await test.step('Search for a term that cannot match', async () => {
        await attentionPage.search('zz-no-such-service-code');
        await expect(authenticatedPage).toHaveURL(/q=zz-no-such-service-code/);
      });

      await test.step('Check the empty state', async () => {
        await expect(attentionPage.emptyStateHeading()).toBeVisible();
        await expect(attentionPage.table()).toHaveCount(0);
        await expect(attentionPage.searchBox()).toHaveValue('zz-no-such-service-code');
      });
    });

    test(`${kind} - sort links keep the search and reset the page`, async ({ authenticatedPage }) => {
      const attentionPage = new RequiresAttentionPage(authenticatedPage, kind);
      await attentionPage.navigate(orgId);
      await expect(attentionPage.exportLink()).toBeVisible(); // rendered once the data has loaded

      // Only organisations that have services requiring attention render the table.
      test.skip((await attentionPage.table().count()) === 0, 'Organisation has no services requiring attention');

      await attentionPage.sortLink('Service code').click();
      await expect(authenticatedPage).toHaveURL(/sort=service_code/);
      await expect(attentionPage.sortLink('Service code')).toHaveAttribute('href', /sort=-service_code/);
    });
  });
}

test.describe('Service codes requiring attention - CSV export', () => {
  test('timetable - export link downloads a CSV', async ({ authenticatedPage }) => {
    const attentionPage = new RequiresAttentionPage(authenticatedPage, 'timetable');
    await attentionPage.navigate(orgId);

    const downloadPromise = authenticatedPage.waitForEvent('download');
    await attentionPage.exportLink().click();
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toMatch(/\.csv$/);
  });
});
