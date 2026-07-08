import { expect, Page, test as base } from '@playwright/test';
import { config } from './config';

type Fixtures = {
  authenticatedPage: Page;
};

export const test = base.extend<Fixtures>({
  authenticatedPage: async ({ page }, use) => {
    if (!config.testUser.username || !config.testUser.password) {
      throw new Error('TEST_USERNAME and TEST_PASSWORD are required for authenticated tests.');
    }

    await use(page);
  },
});

export { expect };