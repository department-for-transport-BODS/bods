/** @jest-environment node */

import { NextRequest } from 'next/server';
import { GET } from './route';
import { forwardToDjango } from '@/lib/django-gateway';

jest.mock('@/lib/django-gateway', () => ({
  forwardToDjango: jest.fn(),
}));

jest.mock('next/navigation', () => ({
  notFound: () => {
    throw new Error('NEXT_HTTP_ERROR_FALLBACK;404');
  },
}));

const mockForward = forwardToDjango as jest.Mock;
const request = new NextRequest('http://data.localhost:3000/catalogue');

describe('data catalogue route', () => {
  beforeEach(() => jest.clearAllMocks());

  it('forwards to Django /catalogue/ on the data host', async () => {
    mockForward.mockResolvedValue(new Response('xlsx'));

    await GET(request);

    expect(mockForward).toHaveBeenCalledWith(
      request,
      '/catalogue/',
      expect.stringMatching(/^data\./),
    );
  });

  it('streams the file and preserves Content-Disposition and Content-Type', async () => {
    mockForward.mockResolvedValue(
      new Response('file-bytes', {
        status: 200,
        headers: {
          'Content-Type': 'application/zip',
          'Content-Disposition': 'attachment; filename="data_catalogue.zip"',
        },
      }),
    );

    const response = await GET(request);

    expect(response.status).toBe(200);
    expect(response.headers.get('Content-Disposition')).toBe(
      'attachment; filename="data_catalogue.zip"',
    );
    expect(response.headers.get('Content-Type')).toBe('application/zip');
    expect(await response.text()).toBe('file-bytes');
  });

  it('passes through the signed-URL redirect when direct S3 URLs are active', async () => {
    mockForward.mockResolvedValue(
      new Response(null, {
        status: 302,
        headers: { Location: 'https://cdn.example.test/data-catalogue/file.zip?sig=abc' },
      }),
    );

    const response = await GET(request);

    expect(response.status).toBe(302);
    expect(response.headers.get('Location')).toBe(
      'https://cdn.example.test/data-catalogue/file.zip?sig=abc',
    );
  });

  it('drops encoding headers that no longer describe the decoded body', async () => {
    mockForward.mockResolvedValue(
      new Response('decoded', {
        headers: { 'Content-Encoding': 'gzip', 'Content-Length': '3' },
      }),
    );

    const response = await GET(request);

    expect(response.headers.get('Content-Encoding')).toBeNull();
    expect(response.headers.get('Content-Length')).toBeNull();
  });

  it('renders the 404 page when no catalogue has been uploaded', async () => {
    mockForward.mockResolvedValue(new Response('Not found', { status: 404 }));

    await expect(GET(request)).rejects.toThrow('NEXT_HTTP_ERROR_FALLBACK;404');
  });
});
