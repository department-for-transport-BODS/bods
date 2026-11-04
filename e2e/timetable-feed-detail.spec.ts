import { test, expect } from './fixtures';
import { TimetableFeedDetailPage } from './pages/TimetableFeedDetailPage';

/*
  Publish timetable feed detail page, linked from "Review my data".
  Needs a live timetable data set owned by the test organisation.
*/
test.describe('Timetable Feed Detail (Authenticated)', () => {
  const testOrgId = process.env.TEST_ORGANISATION_ID || '1';
  const liveDatasetId = process.env.TEST_TIMETABLE_DATASET_ID || '1';

  test('loads the data set details page', async ({ authenticatedPage }) => {
    const detailPage = new TimetableFeedDetailPage(authenticatedPage);
    await detailPage.navigate(testOrgId, liveDatasetId);
    await detailPage.verifyOnPage();
    expect(await detailPage.hasLoaded()).toBe(true);
    expect(await detailPage.getTitle()).toContain('Data set details');
  });

  test('shows the property table rows and actions', async ({ authenticatedPage }) => {
    const detailPage = new TimetableFeedDetailPage(authenticatedPage);
    await detailPage.navigate(testOrgId, liveDatasetId);
    await detailPage.verifyOnPage();
    await detailPage.verifyPropertyRows(['Name', 'Data set ID', 'Status', 'Owner', 'Last updated']);
    await detailPage.verifyUpdateAndDeactivateActions();
    await detailPage.verifyHelpSidebar();
  });

  test('Update data set opens the update journey', async ({ authenticatedPage }) => {
    const detailPage = new TimetableFeedDetailPage(authenticatedPage);
    await detailPage.navigate(testOrgId, liveDatasetId);
    await detailPage.verifyOnPage();
    await detailPage.clickUpdateDataSet();
    await expect(authenticatedPage).toHaveURL(new RegExp(`/dataset/timetable/${liveDatasetId}/update`));
  });
});
