import { test as base } from '@playwright/test';
import { createAuthHelper } from '../helpers/auth';

/**
 * Custom fixtures for authenticated sessions
 * Uses the centralized AuthHelper for consistent authentication
 */

type AuthFixtures = {
  authenticatedPage: any;
};

export const test = base.extend<AuthFixtures>({
  authenticatedPage: async ({ page }, use) => {
    // Use centralized auth helper
    const auth = createAuthHelper(page);
    await auth.login();

    await use(page);
  },
});

export { expect } from '@playwright/test';
