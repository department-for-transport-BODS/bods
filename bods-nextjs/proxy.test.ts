/** @jest-environment node */

import { NextRequest } from 'next/server';
import { proxy } from './proxy';

function request(url: string, host: string, extraHeaders?: Record<string, string>): NextRequest {
  return new NextRequest(url, { headers: { host, ...extraHeaders } });
}

describe('subdomain routing proxy', () => {
  const originalBaseDomain = process.env.NEXT_PUBLIC_BODS_BASE_DOMAIN;

  afterEach(() => {
    process.env.NEXT_PUBLIC_BODS_BASE_DOMAIN = originalBaseDomain;
  });

  describe('deployed hosts', () => {
    beforeEach(() => {
      process.env.NEXT_PUBLIC_BODS_BASE_DOMAIN = 'xyz.com';
    });

    it('rewrites clean publish URLs to the internal publish route', () => {
      const url = 'https://publish.xyz.com/org/42';
      const response = proxy(request(url, 'publish.xyz.com'));

      expect(new URL(response.headers.get('x-middleware-rewrite')!, url).pathname).toBe('/publish/org/42');
    });

    it('rewrites operator requirements on the publish host without losing the section query', () => {
      const url = 'https://publish.xyz.com/guidance/operator-requirements?section=dataquality';
      const response = proxy(request(url, 'publish.xyz.com'));
      const rewriteUrl = new URL(response.headers.get('x-middleware-rewrite')!, url);

      expect(rewriteUrl.pathname).toBe('/publish/guidance/operator-requirements');
      expect(rewriteUrl.search).toBe('?section=dataquality');
    });

    it('rewrites local authority requirements on the publish host without losing the section query', () => {
      const url = 'https://publish.xyz.com/guidance/local-authority-requirements?section=support';
      const response = proxy(request(url, 'publish.xyz.com'));
      const rewriteUrl = new URL(response.headers.get('x-middleware-rewrite')!, url);

      expect(rewriteUrl.pathname).toBe('/publish/guidance/local-authority-requirements');
      expect(rewriteUrl.search).toBe('?section=support');
    });

    it('rewrites developer requirements on the data host without losing the section query', () => {
      const url = 'https://data.xyz.com/guidance/requirements?section=api';
      const response = proxy(request(url, 'data.xyz.com'));
      const rewriteUrl = new URL(response.headers.get('x-middleware-rewrite')!, url);

      expect(rewriteUrl.pathname).toBe('/data/guidance/requirements');
      expect(rewriteUrl.search).toBe('?section=api');
    });

    it('redirects a legacy publish path to the clean publish URL', () => {
      const response = proxy(request('https://publish.xyz.com/publish/org/42?tab=draft', 'publish.xyz.com'));

      expect(response.status).toBe(307);
      expect(response.headers.get('location')).toBe('https://publish.xyz.com/org/42?tab=draft');
    });

    it('rewrites clean data URLs to the internal data route', () => {
      const url = 'https://data.xyz.com/dataset';
      const response = proxy(request(url, 'data.xyz.com'));

      expect(new URL(response.headers.get('x-middleware-rewrite')!, url).pathname).toBe('/data/dataset');
    });

    it('redirects a legacy publish path from the data host to publish', () => {
      const response = proxy(request('https://data.xyz.com/publish/org/42', 'data.xyz.com'));

      expect(response.headers.get('location')).toBe('https://publish.xyz.com/org/42');
    });

    it('redirects shared routes from the publish host to WWW', () => {
      const response = proxy(request('https://publish.xyz.com/contact', 'publish.xyz.com'));

      expect(response.headers.get('location')).toBe('https://www.xyz.com/contact');
    });

    it('leaves www pages on their existing route', () => {
      const response = proxy(request('https://www.xyz.com/contact', 'www.xyz.com'));

      expect(response.headers.get('x-middleware-rewrite')).toBeNull();
      expect(response.headers.get('location')).toBeNull();
    });

    it('leaves the apex domain on its existing route', () => {
      const response = proxy(request('https://xyz.com/', 'xyz.com'));

      expect(response.headers.get('x-middleware-rewrite')).toBeNull();
      expect(response.headers.get('location')).toBeNull();
    });

    it('rewrites publish account to the internal publish account page', () => {
      const url = 'https://publish.xyz.com/account';
      const response = proxy(request(url, 'publish.xyz.com'));

      expect(new URL(response.headers.get('x-middleware-rewrite')!, url).pathname).toBe('/publish/account');
    });

    it('redirects publish login to the www account login page', () => {
      const response = proxy(request('https://publish.xyz.com/account/login', 'publish.xyz.com'));

      expect(response.headers.get('location')).toBe('https://www.xyz.com/account/login');
    });

    it('redirects data /account to the publish account page', () => {
      const response = proxy(request('https://data.xyz.com/account', 'data.xyz.com'));

      expect(response.headers.get('location')).toBe('https://publish.xyz.com/account');
    });

    it('does not redirect using an untrusted host', () => {
      const response = proxy(request('https://publish.evil.com/contact', 'publish.evil.com'));

      expect(response.headers.get('location')).toBeNull();
      expect(response.headers.get('x-middleware-rewrite')).toBeNull();
    });

    it('prefers the Host header over a spoofed forwarded host', () => {
      const response = proxy(
        request('https://publish.xyz.com/contact', 'publish.xyz.com', {
          'x-forwarded-host': 'publish.evil.com',
        }),
      );

      expect(response.headers.get('location')).toBe('https://www.xyz.com/contact');
    });
  });

  describe('local hosts', () => {
    beforeEach(() => {
      process.env.NEXT_PUBLIC_BODS_BASE_DOMAIN = 'localhost';
    });

    it('routes legacy local data paths to the local data hostname', () => {
      const response = proxy(request('http://localhost:3000/data/timetables', 'localhost:3000'));

      expect(response.headers.get('location')).toBe('http://data.localhost:3000/timetables');
    });
  });
});
