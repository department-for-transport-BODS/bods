import path from 'path';
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
  // single authenticated browser context/page per worker for testing
  authenticatedPage: [
    async ({ browser }, use) => {
      const context = await browser.newContext({
        recordVideo: {
          dir: path.resolve(process.cwd(), 'test-results/videos'),
          size: { width: 1280, height: 720 },
        },
      });
      const page = await context.newPage();

      // Use centralized auth helper to sign in once per worker
      const auth = createAuthHelper(page);
      await auth.login();

      await use(page);

      
      const video = page.video();
      await context.close();
      if (video) {
        console.log(`Saved whole-run video: ${await video.path()}`);
      }
    },
    { scope: 'worker' },
  ],
});

export { expect } from '@playwright/test';
