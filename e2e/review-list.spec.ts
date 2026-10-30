import { test, expect } from './fixtures';
import { config } from './config';
import { ReviewListPage, ReviewListKind } from './pages/ReviewListPage';

/*
  "Review my data" list pages (DBODS-2966). The pages mirror Django's
  publish_list_base.html: blue banner, data type selector, tabs, sortable table.
*/
test.describe('Review my data (Authenticated)', () => {
  const orgId = config.organisationId;

  const kinds: { kind: ReviewListKind; heading: RegExp; columns: string[] }[] = [
    {
      kind: 'timetable',
      heading: /Review .* timetables data/i,
      columns: ['Status', 'Data set name', 'Data set ID', 'Last updated', 'Short description'],
    },
    {
      kind: 'avl',
      heading: /Review .* bus location data/i,
      columns: [
        'Status',
        'AVL to Timetable matching',
        'Data feed name',
        'Data feed ID',
        'Last automated update',
        'Short description',
      ],
    },
    {
      kind: 'fares',
      heading: /Review .* fares data/i,
      columns: ['Status', 'Data set name', 'Data set ID', 'Last updated', 'Short description'],
    },
  ];

  for (const { kind, heading, columns } of kinds) {
    test(`${kind} - shows banner, tabs and Django table columns`, async ({ authenticatedPage }) => {
      const reviewList = new ReviewListPage(authenticatedPage);
      await reviewList.navigate(orgId, kind);
      await reviewList.verifyOnPage();

      expect(await reviewList.getHeading()).toMatch(heading);
      expect(await reviewList.bannerStatCount()).toBeGreaterThan(0);
      await expect(authenticatedPage.getByRole('link', { name: 'Active', exact: true })).toBeVisible();
      await expect(authenticatedPage.getByRole('link', { name: 'Draft', exact: true })).toBeVisible();
      await expect(authenticatedPage.getByRole('link', { name: 'Inactive', exact: true })).toBeVisible();

      if (await reviewList.hasNoDataMessage()) {
        return;
      }
      expect(await reviewList.columnHeaders()).toEqual(columns);
    });
  }

  test('timetable - banner shows the three Django stats', async ({ authenticatedPage }) => {
    const reviewList = new ReviewListPage(authenticatedPage);
    await reviewList.navigate(orgId, 'timetable');
    await reviewList.verifyOnPage();

    expect(await reviewList.bannerStatCount()).toBe(3);
  });

  test('timetable - sorting by a column flips direction and keeps the tab', async ({
    authenticatedPage,
  }) => {
    const reviewList = new ReviewListPage(authenticatedPage);
    await reviewList.navigate(orgId, 'timetable', 'tab=draft');
    await reviewList.verifyOnPage();
    test.skip(await reviewList.hasNoDataMessage(), 'No draft datasets for this organisation');

    await reviewList.sortBy('Data set name');
    await expect(authenticatedPage).toHaveURL(/sort=name/);
    await expect(authenticatedPage).toHaveURL(/tab=draft/);
    expect(await reviewList.sortedColumn()).toEqual({
      label: 'Data set name',
      direction: 'ascending',
    });

    await reviewList.sortBy('Data set name');
    await expect(authenticatedPage).toHaveURL(/sort=-name/);
    expect((await reviewList.sortedColumn())?.direction).toBe('descending');
  });

  test('switching tabs keeps you on the same data type', async ({ authenticatedPage }) => {
    const reviewList = new ReviewListPage(authenticatedPage);
    await reviewList.navigate(orgId, 'avl');
    await reviewList.verifyOnPage();

    await reviewList.selectTab('draft');
    await expect(authenticatedPage).toHaveURL(/\/dataset\/avl/);
  });

  test('data type selector moves between the three lists', async ({ authenticatedPage }) => {
    const reviewList = new ReviewListPage(authenticatedPage);
    await reviewList.navigate(orgId, 'timetable');
    await reviewList.verifyOnPage();

    await reviewList.selectDataType('Fares data');
    await expect(authenticatedPage).toHaveURL(/\/dataset\/fares/);
    await reviewList.verifyOnPage();

    await reviewList.selectDataType('Bus location data');
    await expect(authenticatedPage).toHaveURL(/\/dataset\/avl/);
  });
});
