import { test, expect } from '@playwright/test';
import { config } from '../config';
import { HomePage } from '../pages/HomePage';

test.describe('Basic Functionality', () => {
    /*
    These are just basic proof of concept tests to prove that the test ssteup is working.
    More comprehensive/bespoke tests should be added in their own files.
    */
  test('homepage loads successfully', async ({ page }) => {
    await page.goto(config.baseUrl);
    expect(page.url()).toContain(config.baseUrl);
  });

  test('homepage has correct title', async ({ page }) => {
    await page.goto(config.baseUrl);
    const title = await page.title();
    expect(title).toContain('Bus Open Data Service');
  });
});
