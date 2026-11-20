import { config } from './config';
import { expect, test } from './fixtures';

const BODS_SUBDOMAINS = new Set(['www', 'data', 'publish', 'admin']);

function dataUrl(pathname: string): string {
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

test.describe('Swagger pages', () => {
  test('API overview pages load and link to their documentation', async ({ authenticatedPage }) => {
    const overviewPages = [
      {
        path: '/api/buslocation-api/',
        heading: 'Location data API Service',
        documentationLink: 'Try API',
      },
      {
        path: '/api/disruptions-api-overview/',
        heading: 'Disruptions data API',
        documentationLink: 'Try the disruptions data API',
      },
      {
        path: '/api/cancellations-api-overview/',
        heading: 'Cancellations data API',
        documentationLink: 'Try the cancellations data API',
      },
    ];

    for (const overview of overviewPages) {
      await test.step(`Load ${overview.heading} overview`, async () => {
        await authenticatedPage.goto(dataUrl(overview.path));

        await expect(
          authenticatedPage.getByRole('heading', { level: 1, name: overview.heading }),
        ).toHaveCount(1);
        await expect(
          authenticatedPage.getByRole('link', { name: overview.documentationLink }),
        ).toHaveCount(1);
      });
    }
  });

  test('Swagger UI loads on each API documentation page', async ({ authenticatedPage }) => {
    const documentationPages = [
      '/api/timetable-openapi/',
      '/api/buslocation-api/openapi/',
      '/api/fares-openapi/',
      '/api/disruptions-openapi/',
      '/api/cancellations-openapi/',
    ];

    for (const path of documentationPages) {
      await test.step(`Load Swagger UI at ${path}`, async () => {
        await authenticatedPage.goto(dataUrl(path));

        await expect(authenticatedPage.locator('#swagger-ui .swagger-ui')).toHaveCount(1);
      });
    }
  });
});