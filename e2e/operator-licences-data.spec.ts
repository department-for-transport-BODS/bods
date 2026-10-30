import { test, expect } from '@playwright/test';
import { config } from './config';
import { OperatorsPage } from './pages/OperatorsPage';
import { OperatorDetailPage } from './pages/OperatorDetailPage';
import { OperatorLicencePage } from './pages/OperatorLicencePage';

test.describe('Operator licence pages (Unauthenticated)', () => {
  test('operator profile licence links open the licence page with Django copy', async ({ page }) => {
    const operators = new OperatorsPage(page);
    await operators.navigate();
    await operators.openFirstOperator();
    await new OperatorDetailPage(page).verifyOnPage();

    const licenceLink = page.locator('a[href*="/operators/licence/"]').first();
    test.skip((await licenceLink.count()) === 0, 'First operator has no licences to open');
    await licenceLink.click();

    const licence = new OperatorLicencePage(page);
    await licence.verifyOnPage();
    await expect(licence.heading).toContainText(' - ');
    await expect(page).toHaveTitle(/Operator Licence details/);
    await expect(licence.breadcrumbs.getByRole('link', { name: 'Operator Profiles' })).toBeVisible();
    await expect(page.getByText('Overview of the available bus open data')).toBeVisible();
    await expect(page.getByRole('rowheader', { name: 'Owner' })).toBeVisible();
    await expect(licence.reviewServiceNumbersHeading).toBeVisible();
    await expect(page.getByRole('heading', { level: 2, name: 'What you need to know' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'View developer documentation' })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Contact us for technical issues' })).toBeVisible();
  });

  test('licence page filters and service list open the service page', async ({ page }) => {
    const operators = new OperatorsPage(page);
    await operators.navigate();
    await operators.openFirstOperator();
    const licenceLink = page.locator('a[href*="/operators/licence/"]').first();
    test.skip((await licenceLink.count()) === 0, 'First operator has no licences to open');
    await licenceLink.click();

    const licence = new OperatorLicencePage(page);
    await licence.verifyOnPage();
    test.skip((await licence.serviceLinks.count()) === 0, 'Licence has no services to open');

    await expect(licence.checkbox('In Scope')).toBeChecked();
    await expect(licence.checkbox('Out of scope')).not.toBeChecked();
    await licence.checkbox('Out of scope').check();
    await expect(licence.checkbox('Out of scope')).toBeChecked();

    const service = await licence.openFirstService();
    await service.verifyOnPage();
    await expect(service.breadcrumbs.getByRole('link', { name: 'Operator Profiles' })).toBeVisible();
    await expect(page.getByText('Overview of the available bus open data')).toBeVisible();
    await expect(page.getByRole('rowheader', { name: 'Type of service' })).toBeVisible();
  });

  test('unknown licence shows the not found page', async ({ page }) => {
    await page.goto(`${config.baseUrl}/data/operators/licence/ZZ0000000`);
    await expect(page.getByRole('heading', { name: /page not found/i })).toBeVisible();
  });
});
