import { expect, test } from '@playwright/test';
import { LoginPage } from './pages/LoginPage';

test.describe('Login validation errors', () => {
  test('matches Django inline errors and suppresses native browser validation', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await test.step('Open the login page and submit empty fields', async () => {
      await loginPage.navigate();
      await loginPage.verifyOnPage();
      await expect(page).toHaveTitle('Sign in');
      await loginPage.submit();
    });

    await test.step('Verify the focused Django-style error summary', async () => {
      const summary = page.getByRole('alert', { name: 'There is a problem' });
      await expect(summary).toContainText('There is a problem');
      await expect(summary).toBeFocused();
      await expect(summary.getByRole('link', { name: 'Please provide an email' }))
        .toHaveAttribute('href', '#id_login');
      await expect(summary.getByRole('link', { name: 'Please provide a password' }))
        .toHaveAttribute('href', '#id_password');
    });

    await test.step('Verify inline error order, GOV.UK error styles and noValidate', async () => {
      const emailError = page.locator('[id="1_id_login-error"]');
      const emailInput = loginPage.emailInput;
      const emailGroup = emailInput.locator('xpath=..');
      await expect(emailGroup).toHaveClass(/govuk-form-group--error/);
      await expect(emailInput).toHaveClass(/govuk-input--error/);
      await expect(emailError).toHaveText('Please provide an email');
      expect(
        await emailError.evaluate((error) =>
          Boolean(
            error.compareDocumentPosition(document.querySelector('#id_login')!) &
              Node.DOCUMENT_POSITION_FOLLOWING,
          ),
        ),
      ).toBe(true);

      const passwordError = page.locator('[id="1_id_password-error"]');
      const passwordInput = loginPage.passwordInput;
      const passwordGroup = passwordInput.locator('xpath=..');
      await expect(passwordGroup).toHaveClass(/govuk-form-group--error/);
      await expect(passwordInput).toHaveClass(/govuk-input--error/);
      await expect(passwordError).toHaveText('Please provide a password');
      await expect(passwordInput).toHaveAttribute('aria-describedby', 'id_password-hint');
      await expect(page.locator('form')).toHaveAttribute('novalidate', '');
    });
  });
});
