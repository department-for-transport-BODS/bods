/** @jest-environment node */

import { NextRequest } from 'next/server';
import { GET as getMatchingReport, HEAD as headMatchingReport } from '@/app/publish/org/[orgId]/dataset/avl/[datasetId]/download-matching-report/route';
import { GET as getPpcArchive, HEAD as headPpcArchive } from '@/app/publish/org/[orgId]/dataset/ppc-archive/route';

const mockFetch = jest.fn();

describe('PPC download route handlers', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    mockFetch.mockReset();
    global.fetch = mockFetch as unknown as typeof fetch;
  });

  afterAll(() => {
    global.fetch = originalFetch;
  });

  describe('ppc-archive', () => {
    const request = new NextRequest('http://publish.localhost:3000/org/1/dataset/ppc-archive?x=1', {
      headers: { cookie: 'sessionid=abc' },
    });
    const context = { params: Promise.resolve({ orgId: '1' }) };

    it('proxies to the Django publish PPC archive view and passes the zip response through', async () => {
      const upstream = new Response('zip-bytes', {
        status: 200,
        headers: {
          'content-type': 'application/zip',
          'content-disposition':
            'attachment; filename=archived_avl_to_timetable_matching_all_feeds.zip',
        },
      });
      mockFetch.mockResolvedValue(upstream);

      const response = await getPpcArchive(request, context);

      expect(response).toBe(upstream);
      const [url, init] = mockFetch.mock.calls[0];
      expect(new URL(url).pathname).toBe('/org/1/dataset/ppc-archive/');
      expect(new URL(url).search).toBe('?x=1');
      expect(init.method).toBe('GET');
      expect(init.redirect).toBe('manual');
      expect(new Headers(init.headers).get('cookie')).toBe('sessionid=abc');
      expect(new Headers(init.headers).get('host')).toMatch(/^publish\./);
      expect(response.headers.get('content-disposition')).toBe(
        'attachment; filename=archived_avl_to_timetable_matching_all_feeds.zip',
      );
      expect(await response.text()).toBe('zip-bytes');
    });

    it('passes Django redirects through without following them', async () => {
      mockFetch.mockResolvedValue(
        new Response(null, { status: 302, headers: { location: '/account/login/?next=/x/' } }),
      );

      const response = await getPpcArchive(request, context);

      expect(response.status).toBe(302);
      expect(response.headers.get('location')).toBe('/account/login/?next=/x/');
    });

    it('passes Django 404 and 500 responses through', async () => {
      mockFetch.mockResolvedValueOnce(new Response('missing', { status: 404 }));
      expect((await getPpcArchive(request, context)).status).toBe(404);

      mockFetch.mockResolvedValueOnce(new Response('boom', { status: 500 }));
      expect((await getPpcArchive(request, context)).status).toBe(500);
    });

    it('supports HEAD requests', async () => {
      mockFetch.mockResolvedValue(new Response(null, { status: 200 }));
      const headRequest = new NextRequest(request.url, { method: 'HEAD' });

      await headPpcArchive(headRequest, context);

      expect(mockFetch.mock.calls[0][1].method).toBe('HEAD');
    });

    it('does not proxy a non-numeric organisation id', async () => {
      const response = await getPpcArchive(request, {
        params: Promise.resolve({ orgId: '1/../account' }),
      });

      expect(response.status).toBe(404);
      expect(mockFetch).not.toHaveBeenCalled();
    });
  });

  describe('avl download-matching-report', () => {
    const request = new NextRequest(
      'http://publish.localhost:3000/org/1/dataset/avl/9/download-matching-report',
      { headers: { cookie: 'sessionid=abc' } },
    );
    const context = { params: Promise.resolve({ orgId: '1', datasetId: '9' }) };

    it('proxies to the Django matching report view and keeps the attachment headers', async () => {
      mockFetch.mockResolvedValue(
        new Response('a,b', {
          status: 200,
          headers: {
            'content-type': 'text/csv',
            'content-disposition': 'attachment; filename=report.csv',
          },
        }),
      );

      const response = await getMatchingReport(request, context);

      const [url, init] = mockFetch.mock.calls[0];
      expect(new URL(url).pathname).toBe('/org/1/dataset/avl/9/download-matching-report/');
      expect(init.redirect).toBe('manual');
      expect(new Headers(init.headers).get('cookie')).toBe('sessionid=abc');
      expect(response.status).toBe(200);
      expect(response.headers.get('content-type')).toBe('text/csv');
      expect(response.headers.get('content-disposition')).toBe('attachment; filename=report.csv');
      expect(await response.text()).toBe('a,b');
    });

    it('passes Django redirects, 404 and error responses through', async () => {
      mockFetch.mockResolvedValueOnce(
        new Response(null, { status: 302, headers: { location: '/account/login/' } }),
      );
      const redirect = await getMatchingReport(request, context);
      expect(redirect.status).toBe(302);
      expect(redirect.headers.get('location')).toBe('/account/login/');

      mockFetch.mockResolvedValueOnce(new Response('missing', { status: 404 }));
      expect((await getMatchingReport(request, context)).status).toBe(404);

      mockFetch.mockResolvedValueOnce(new Response('boom', { status: 500 }));
      expect((await getMatchingReport(request, context)).status).toBe(500);
    });

    it('supports HEAD requests', async () => {
      mockFetch.mockResolvedValue(new Response(null, { status: 200 }));

      await headMatchingReport(new NextRequest(request.url, { method: 'HEAD' }), context);

      expect(mockFetch.mock.calls[0][1].method).toBe('HEAD');
    });

    it.each([
      ['1/../account', '9'],
      ['1', '9/../x'],
      ['abc', '9'],
    ])('does not proxy invalid ids (%s, %s)', async (orgId, datasetId) => {
      const response = await getMatchingReport(request, {
        params: Promise.resolve({ orgId, datasetId }),
      });

      expect(response.status).toBe(404);
      expect(mockFetch).not.toHaveBeenCalled();
    });
  });
});
