import { Locator, Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';
import { dataUrl } from './DataDownloadsPage';

export type BrowseDatasetType = 'timetable' | 'avl' | 'fares';

/** Data host dataset browsing at Django's public URLs: /timetable/, /avl/, /fares/ and /<type>/dataset/<id>. */
export class DatasetBrowsePage extends BasePage {
  readonly notFoundHeading: Locator;

  constructor(page: Page) {
    super(page);
    this.notFoundHeading = page.getByRole('heading', { level: 1, name: 'Page not found' });
  }

  async openList(type: BrowseDatasetType, query = ''): Promise<this> {
    await this.page.goto(`${dataUrl(`/${type}`)}${query}`);
    return this;
  }

  async openPath(pathname: string): Promise<number> {
    const response = await this.page.goto(dataUrl(pathname));
    return response?.status() ?? 0;
  }

  async openSearch(): Promise<this> {
    await this.page.goto(dataUrl('/search'));
    return this;
  }

  listLink(name: string | RegExp): Locator {
    return this.page.getByRole('link', { name, exact: typeof name === 'string' });
  }

  datasetLinks(type: BrowseDatasetType): Locator {
    return this.page.locator(`a[href*="/${type}/dataset/"]`);
  }

  async expectOnList(type: BrowseDatasetType): Promise<this> {
    await expect(this.page).toHaveURL(new RegExp(`/${type}/?(\\?.*)?$`));
    await expect(this.page.getByRole('heading', { level: 1 })).toBeVisible();
    return this;
  }
}
