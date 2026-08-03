import { test, expect } from './fixtures';
import { config } from '../config';
import { OrganisationProfilePage } from '../pages/OrganisationProfilePage';

/*
  Each of these tests uses the authenticatedPage fixture, which means that the logic is that everything here happens after login.
  The actual login logic is encapsulated in the AuthHelper class in helpers/auth.ts, promoting reuse and maintainability.
  For the time being that pattern should be kept to avoid duplicating login logic across multiple test files/ making easy maintainability across different services.
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
