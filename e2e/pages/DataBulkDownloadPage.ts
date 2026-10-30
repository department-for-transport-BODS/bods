import { Locator, Page, expect } from '@playwright/test';
import { config } from '../config';
import { BasePage } from './BasePage';

const BODS_SUBDOMAINS = new Set(['www', 'data', 'publish', 'admin']);

export type BulkDownloadKind = 'timetable' | 'avl' | 'fares' | 'disruptions' | 'coach';

/** Data-host URL derived from PLAYWRIGHT_BASE_URL (localhost or a deployed env). */
function dataHostUrl(pathname: string): string {
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

const PAGES: Record<BulkDownloadKind, { path: string; title: string }> = {
  timetable: { path: '/timetable/download/', title: 'All timetables data' },
  avl: { path: '/avl/download/', title: 'All location data' },
  fares: { path: '/fares/download/', title: 'All fares data' },
  disruptions: { path: '/disruptions/download/', title: 'All disruption data' },
  coach: { path: '/coach/download', title: 'All coach data' },
};

/** Data host bulk-download pages: /timetable|avl|fares|disruptions|coach/download. */
export class DataBulkDownloadPage extends BasePage {
  readonly kind: BulkDownloadKind;
  readonly heading: Locator;

  constructor(page: Page, kind: BulkDownloadKind) {
    super(page);
    this.kind = kind;
    // Django's h1 carries aria-label="Heading Title", so match on its text, not its accessible name.
    this.heading = page.locator('h1.govuk-heading-xl', { hasText: PAGES[kind].title });
  }

  get path(): string {
    return PAGES[this.kind].path;
  }

  async open(): Promise<this> {
    await this.page.goto(dataHostUrl(this.path));
    return this;
  }

  async verifyLoaded(): Promise<this> {
    await expect(this.heading).toBeVisible();
    await expect(this.page.getByRole('link', { name: 'Service changelog' })).toBeVisible();
    return this;
  }

  async verifyRedirectedToLogin(): Promise<this> {
    await expect(this.page).toHaveURL(/\/account\/login\//);
    return this;
  }

  /** Every download link on the page that points at a Django file route. */
  fileLinks(): Locator {
    return this.page.locator(`main a[href*="/${this.kind}/download/"]`);
  }

  async openHelpModal(formatName: string): Promise<this> {
    await this.page.getByRole('button', { name: `Help: ${formatName}` }).first().click();
    return this;
  }
}
