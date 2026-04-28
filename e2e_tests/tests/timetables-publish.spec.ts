import { test, expect } from './fixtures';
import { config } from '../config';
import { TimetablePublishPage } from '../pages/TimetablePublishPage';
import { TimetableReviewPage } from '../pages/TimetableReviewPage';

/*
  Each test uses the authenticatedPage fixture, so the user is logged in before each test runs.
  The login logic is handled by AuthHelper in helpers/auth.ts.
*/
test.describe('Timetable Publish Flow (Authenticated)', () => {

  const testOrgId = '1';

  test('can load timetable publish page', async ({ authenticatedPage }) => {
    const publishPage = new TimetablePublishPage(authenticatedPage);
    await publishPage.navigate(testOrgId);
    await publishPage.verifyOnPage();
    expect(await publishPage.hasLoaded()).toBe(true);
  });

  test('step 1 - describe data set is displayed', async ({ authenticatedPage }) => {
    const publishPage = new TimetablePublishPage(authenticatedPage);
    await publishPage.navigate(testOrgId);
    await publishPage.verifyStep1Visible();
  });

  test('step 1 - shows validation errors when fields are empty', async ({ authenticatedPage }) => {
    const publishPage = new TimetablePublishPage(authenticatedPage);
    await publishPage.navigate(testOrgId);
    await publishPage.verifyStep1Visible();
    await publishPage.clickContinue();
    expect(await publishPage.hasErrorMessage()).toBe(true);
  });

  test('step 1 - can fill description and advance to step 2', async ({ authenticatedPage }) => {
    const publishPage = new TimetablePublishPage(authenticatedPage);
    await publishPage.navigate(testOrgId);
    await publishPage.verifyStep1Visible();
    await publishPage.fillStep1('Test timetable dataset description', 'Short desc');
    await publishPage.clickContinue();
    await publishPage.verifyStep2Visible();
  });

  test('step 2 - shows validation errors when no method selected', async ({ authenticatedPage }) => {
    const publishPage = new TimetablePublishPage(authenticatedPage);
    await publishPage.navigate(testOrgId);
    await publishPage.fillStep1('Test dataset', 'Short desc');
    await publishPage.clickContinue();
    await publishPage.verifyStep2Visible();
    // Try continuing without selecting a method
    await publishPage.clickContinue();
    expect(await publishPage.hasErrorMessage()).toBe(true);
  });

  test('step 2 - can select URL link option and advance to step 3', async ({ authenticatedPage }) => {
    const publishPage = new TimetablePublishPage(authenticatedPage);
    await publishPage.navigate(testOrgId);
    await publishPage.fillStep1('Test dataset', 'Short desc');
    await publishPage.clickContinue();
    await publishPage.verifyStep2Visible();
    await publishPage.selectUrlLink();
    await publishPage.fillUrlLink('https://example.com/timetable.xml');
    await publishPage.clickContinue();
    await publishPage.verifyStep3Visible();
  });

  test('step 3 - displays summary of entered data', async ({ authenticatedPage }) => {
    const publishPage = new TimetablePublishPage(authenticatedPage);
    await publishPage.navigate(testOrgId);
    await publishPage.fillStep1('My timetable data', 'Brief timetable');
    await publishPage.clickContinue();
    await publishPage.selectUrlLink();
    await publishPage.fillUrlLink('https://example.com/data.xml');
    await publishPage.clickContinue();
    await publishPage.verifyStep3Visible();
    await publishPage.verifySummaryContains('My timetable data');
    await publishPage.verifySummaryContains('Brief timetable');
  });

  test('step 3 - consent checkbox can be toggled', async ({ authenticatedPage }) => {
    const publishPage = new TimetablePublishPage(authenticatedPage);
    await publishPage.navigate(testOrgId);
    await publishPage.fillStep1('Dataset', 'Short');
    await publishPage.clickContinue();
    await publishPage.selectUrlLink();
    await publishPage.fillUrlLink('https://example.com/data.xml');
    await publishPage.clickContinue();
    await publishPage.verifyStep3Visible();

    expect(await publishPage.isConsentChecked()).toBe(false);
    await publishPage.checkConsent();
    expect(await publishPage.isConsentChecked()).toBe(true);
  });
});

test.describe('Timetable Review Page (Authenticated)', () => {

  const testOrgId = '1';
  const testDatasetId = '1';

  test('can load timetable review page', async ({ authenticatedPage }) => {
    const reviewPage = new TimetableReviewPage(authenticatedPage);
    await reviewPage.navigate(testOrgId, testDatasetId);
    await reviewPage.verifyOnPage();
    expect(await reviewPage.hasLoaded()).toBe(true);
  });

  test('review page has correct heading', async ({ authenticatedPage }) => {
    const reviewPage = new TimetableReviewPage(authenticatedPage);
    await reviewPage.navigate(testOrgId, testDatasetId);
    const heading = await reviewPage.getHeading();
    expect(heading).toContain('Review and publish');
  });

  test('review page has reviewed checkbox', async ({ authenticatedPage }) => {
    const reviewPage = new TimetableReviewPage(authenticatedPage);
    await reviewPage.navigate(testOrgId, testDatasetId);
    // Wait for processing to complete or page to load
    await authenticatedPage.waitForLoadState('networkidle');

    const checkbox = authenticatedPage.locator('#id_has_reviewed');
    // Checkbox should be present in the DOM (may be hidden if still processing)
    await expect(checkbox).toBeAttached();
  });

  test('review page has back to data sets link', async ({ authenticatedPage }) => {
    const reviewPage = new TimetableReviewPage(authenticatedPage);
    await reviewPage.navigate(testOrgId, testDatasetId);
    await authenticatedPage.waitForLoadState('networkidle');

    const backLink = authenticatedPage.getByRole('link', { name: 'Back to data sets' });
    await expect(backLink).toBeAttached();
  });
});
