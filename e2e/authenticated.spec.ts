import { test, expect } from './fixtures';
import { config } from './config';
import { OrganisationProfilePage } from './pages/OrganisationProfilePage';

/*
  Each of these tests uses the authenticatedPage fixture, which means that the logic is that everything here happens after login.
  Login is performed once in global setup and reused through Playwright's saved storage state.
*/
test.describe('Authenticated User Tests', () => {

  test('can load organisation profile page', async ({ authenticatedPage }) => {
    await authenticatedPage.waitForLoadState('networkidle');
    const orgProfilePage = new OrganisationProfilePage(authenticatedPage);
    await orgProfilePage.navigateFromDashboard();
    await orgProfilePage.verifyOnPage();
    expect(await orgProfilePage.hasLoaded()).toBe(true);
    expect((await orgProfilePage.getOrganisationName())?.trim()).toBe(config.testOrganisation.name);
  });
});
