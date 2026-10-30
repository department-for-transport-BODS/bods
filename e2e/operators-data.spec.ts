import { test, expect } from '@playwright/test';
import { config } from './config';
import { OperatorsPage } from './pages/OperatorsPage';
import { OperatorDetailPage } from './pages/OperatorDetailPage';

test.describe('Operator Profiles (Unauthenticated)', () => {
  test('operators list loads with the Django heading, search and sort', async ({ page }) => {
    const operators = new OperatorsPage(page);
    await operators.navigate();
    await operators.verifyOnPage();

    await expect(page.getByText('Search for a specific operator')).toBeVisible();
    await expect(operators.searchInput).toBeVisible();
    await expect(operators.sortSelect.locator('option')).toHaveText([
      'Name A-Z',
      'Name Z-A',
      'Date registered newest',
      'Date registered oldest',
    ]);
  });

  test('operators list can be searched and the search term cleared', async ({ page }) => {
    const operators = new OperatorsPage(page);
    await operators.navigate();
    await operators.searchFor('zzzz-no-such-operator');

    await expect(page).toHaveURL(/q=zzzz-no-such-operator/);
    await expect(page.getByRole('heading', { name: 'Sorry, no results found for zzzz-no-such-operator' })).toBeVisible();
    await expect(page.getByText('Check your spelling and try again')).toBeVisible();
    await expect(page.getByText('Containing')).toBeVisible();
  });

  test('operators list sorting updates the URL', async ({ page }) => {
    const operators = new OperatorsPage(page);
    await operators.navigate();
    await operators.sortBy('Name Z-A');

    await expect(page).toHaveURL(/ordering=-name/);
  });

  test('operators list links through to an operator profile', async ({ page }) => {
    const operators = new OperatorsPage(page);
    await operators.navigate();
    await operators.openFirstOperator();

    const detail = new OperatorDetailPage(page);
    await detail.verifyOnPage();
    await expect(detail.breadcrumbs.getByRole('link', { name: 'Operator Profiles' })).toBeVisible();
    await expect(detail.browseTimetablesLink).toBeVisible();
    await expect(detail.browseLocationLink).toBeVisible();
    await expect(detail.browseFaresLink).toBeVisible();
    await expect(detail.registerLink).toBeVisible();
  });

  test('operators page is navigable from the data home page', async ({ page }) => {
    await page.goto(`${config.baseUrl}/data`);
    await page.getByRole('link', { name: 'View operator profiles' }).click();
    await expect(page).toHaveURL(/\/operators\/?$/);
    await new OperatorsPage(page).verifyOnPage();
  });

  test('unknown operator shows the not found page', async ({ page }) => {
    await page.goto(`${config.baseUrl}/data/operators/99999999`);
    await expect(page.getByRole('heading', { name: /page not found/i })).toBeVisible();
  });

  test('contacting an operator requires sign in', async ({ page }) => {
    await page.goto(`${config.baseUrl}/data/operators/1/contact`);
    await expect(page).toHaveURL(/\/account\/login/);
  });
});
