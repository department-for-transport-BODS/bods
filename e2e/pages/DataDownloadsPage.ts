import { Locator, Page, expect } from '@playwright/test';
import { config } from '../config';
import { BasePage } from './BasePage';

const BODS_SUBDOMAINS = new Set(['www', 'data', 'publish', 'admin']);

/** Public URL on the data host, derived from PLAYWRIGHT_BASE_URL (localhost or a deployed env). */
export function dataUrl(pathname: string): string {
  const url = new URL(config.baseUrl);
  const labels = url.hostname.split('.');

  if (url.hostname === 'localhost') {
    url.hostname = 'data.localhost';
  } else if (BODS_SUBDOMAINS.has(labels[0])) {
    labels[0] = 'data';
    url.hostname = labels.join('.');
  } else {
    url.hostname = `data.${url.hostname}`;
  }

  url.pathname = pathname;
  url.search = '';
  url.hash = '';
  return url.toString();
}

/** Data host `/downloads/` ("Download all data") and the site 404 page. */
export class DataDownloadsPage extends BasePage {
  readonly heading: Locator;
  readonly notFoundHeading: Locator;

  constructor(page: Page) {
    super(page);
    // Django's h1 carries aria-label="Heading Title", so match on its text, not its accessible name.
    this.heading = page.locator('h1', { hasText: 'Download all data' });
    this.notFoundHeading = page.getByRole('heading', { level: 1, name: 'Page not found' });
  }

  async open(): Promise<this> {
    await this.page.goto(dataUrl('/downloads/'));
    return this;
  }

  async openUnknownPath(pathname: string): Promise<number> {
    const response = await this.page.goto(dataUrl(pathname));
    return response?.status() ?? 0;
  }

  downloadLink(name: string): Locator {
    return this.page.getByRole('link', { name, exact: true });
  }

  async verifyDownloadLinks(): Promise<this> {
    await expect(this.heading).toBeVisible();
    for (const [name, path] of [
      ['Download the data catalogue', '/catalogue'],
      ['Timetables data', '/timetable/download'],
      ['Location data', '/avl/download'],
      ['Fares data', '/fares/download'],
      ['Disruptions data', '/disruptions/download'],
      ['Coach data', '/coach/download'],
    ]) {
      await expect(this.downloadLink(name)).toHaveAttribute('href', new RegExp(`${path}/?$`));
    }
    return this;
  }

  async openHelpModal(formatName: string): Promise<this> {
    await this.page.getByRole('button', { name: `Help: ${formatName}` }).first().click();
    return this;
  }
}
