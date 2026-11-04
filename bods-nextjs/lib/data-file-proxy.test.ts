/** @jest-environment node */

import { NextRequest } from 'next/server';
import { forwardToDjango } from '@/lib/django-gateway';
import { forwardDataFile } from './data-file-proxy';

jest.mock('@/lib/django-gateway', () => ({
  forwardToDjango: jest.fn(),
}));

jest.mock('next/navigation', () => ({
  notFound: () => {
    throw new Error('NEXT_HTTP_ERROR_FALLBACK;404');
  },
}));

const mockForward = forwardToDjango as jest.Mock;
const request = new NextRequest('http://data.localhost:3000/timetable/download/bulk_archive');

describe('forwardDataFile', () => {
  beforeEach(() => jest.clearAllMocks());

  it('forwards the path to Django on the data host', async () => {
    mockForward.mockResolvedValue(new Response('zip'));

    await forwardDataFile(request, '/timetable/download/bulk_archive');

    expect(mockForward).toHaveBeenCalledWith(
      request,
      '/timetable/download/bulk_archive',
      expect.stringMatching(/^data\./),
    );
  });

  it('streams the file and keeps Content-Disposition and Content-Type', async () => {
    mockForward.mockResolvedValue(
      new Response('file-bytes', {
        status: 200,
        headers: {
          'Content-Type': 'application/zip',
          'Content-Disposition': 'attachment; filename="bulk_archive.zip"',
        },
      }),
    );

    const response = await forwardDataFile(request, '/x');

    expect(response.status).toBe(200);
    expect(response.headers.get('Content-Disposition')).toBe(
      'attachment; filename="bulk_archive.zip"',
    );
    expect(response.headers.get('Content-Type')).toBe('application/zip');
    expect(await response.text()).toBe('file-bytes');
  });

  it('passes a signed-URL redirect through without following it', async () => {
    const location = 'https://cdn.example.test/bulk_archive.zip?sig=abc';
    mockForward.mockResolvedValue(new Response(null, { status: 302, headers: { Location: location } }));

    const response = await forwardDataFile(request, '/x');

    expect(response.status).toBe(302);
    expect(response.headers.get('Location')).toBe(location);
  });

  it('drops encoding headers that no longer describe the decoded body', async () => {
    mockForward.mockResolvedValue(
      new Response('body', {
        headers: { 'Content-Encoding': 'gzip', 'Content-Length': '4', 'Content-Type': 'text/plain' },
      }),
    );

    const response = await forwardDataFile(request, '/x');

    expect(response.headers.get('Content-Encoding')).toBeNull();
    expect(response.headers.get('Content-Length')).toBeNull();
    expect(response.headers.get('Content-Type')).toContain('text/plain');
  });

  it('shows the site 404 page when Django has no archive', async () => {
    mockForward.mockResolvedValue(new Response('Not found', { status: 404 }));

    await expect(forwardDataFile(request, '/x')).rejects.toThrow('NEXT_HTTP_ERROR_FALLBACK;404');
  });
});
