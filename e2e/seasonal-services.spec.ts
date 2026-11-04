import { test, expect } from './fixtures';
import { config } from './config';
import { SeasonalServicesPage } from './pages/SeasonalServicesPage';

/*
  Seasonal services journey (add, edit dates, delete).
  The test user must belong to an organisation (config.organisationId) with at least one PSV licence.
  The created service uses a timestamp-derived service code and is deleted again by the test.
*/
test.describe('Seasonal Services (Authenticated)', () => {
  const orgId = config.organisationId;

  test('list page loads with the Django page content', async ({ authenticatedPage }) => {
    const seasonal = new SeasonalServicesPage(authenticatedPage);
    await seasonal.navigate(orgId);
    await seasonal.verifyOnList();
    await expect(authenticatedPage).toHaveTitle('Manage seasonal services');
    await expect(authenticatedPage.getByRole('columnheader', { name: 'Actions' })).toBeVisible();
    await expect(authenticatedPage.getByRole('button', { name: 'Close' })).toBeVisible();
  });

  test('add new - step 1 requires a licence', async ({ authenticatedPage }) => {
    const seasonal = new SeasonalServicesPage(authenticatedPage);
    await seasonal.navigateToAddNew(orgId);
    await seasonal.clickContinue();
    await expect(seasonal.errorSummary()).toBeVisible();
    expect(await seasonal.errorSummaryMessages()).toEqual(['This field is required.']);
  });

  test('add new - step 2 shows validation errors', async ({ authenticatedPage }) => {
    const seasonal = new SeasonalServicesPage(authenticatedPage);
    await seasonal.navigateToAddNew(orgId);
    await seasonal.selectLicence(await seasonal.firstLicenceNumber());
    await seasonal.clickContinue();
    await seasonal.verifyStep2Visible();
    await seasonal.clickSave();
    await expect(seasonal.errorSummary()).toBeVisible();
    expect(await seasonal.errorSummaryMessages()).toContain('Enter a service code in the box below');
  });

  test('add, edit dates and delete a seasonal service', async ({ authenticatedPage }) => {
    const seasonal = new SeasonalServicesPage(authenticatedPage);
    const code = String(Date.now()).slice(-8);
    let serviceCode = '';

    await test.step('add a new date range', async () => {
      await seasonal.navigate(orgId);
      await seasonal.clickAddNew();
      const licence = await seasonal.firstLicenceNumber();
      serviceCode = `${licence}/${code}`;
      await seasonal.selectLicence(licence);
      await seasonal.clickContinue();
      await seasonal.verifyStep2Visible();
      await seasonal.fillServiceCode(code);
      await seasonal.fillDates('2098-01-01', '2099-12-31');
      await seasonal.clickSave();
      await expect(authenticatedPage).toHaveURL(/seasonal-service\/?\?page=/);

      await seasonal.sortBy('Service ends');
      await seasonal.sortBy('Service ends');
      await expect(seasonal.rowForServiceCode(serviceCode)).toContainText('31/12/2099');
    });

    await test.step('edit its dates', async () => {
      await seasonal.clickEditDates(serviceCode);
      await expect(authenticatedPage.getByLabel('Service ends on')).toHaveValue('2099-12-31');
      await seasonal.fillDates('2098-01-02', '2099-12-30');
      await seasonal.clickSave();
      await expect(authenticatedPage).toHaveURL(/seasonal-service\/?\?page=/);
      await seasonal.sortBy('Service ends');
      await seasonal.sortBy('Service ends');
      await expect(seasonal.rowForServiceCode(serviceCode)).toContainText('30/12/2099');
    });

    await test.step('delete it', async () => {
      await seasonal.clickDelete(serviceCode);
      await expect(seasonal.rowForServiceCode(serviceCode)).toHaveCount(0);
    });
  });

  test('edit dates - shows validation error when end is before start', async ({ authenticatedPage }) => {
    const seasonal = new SeasonalServicesPage(authenticatedPage);
    await seasonal.navigate(orgId);
    await seasonal.verifyOnList();
    const editLink = authenticatedPage.getByRole('link', { name: 'Edit dates' }).first();
    test.skip((await editLink.count()) === 0, 'No seasonal services to edit for this organisation');
    await editLink.click();
    await seasonal.fillDates('2099-12-31', '2099-01-01');
    await seasonal.clickSave();
    await expect(seasonal.errorSummary()).toBeVisible();
    expect(await seasonal.errorSummaryMessages()).toContain('Start date must be earlier than end date');
  });
});
