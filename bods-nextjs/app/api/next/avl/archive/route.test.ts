/** @jest-environment node */

import { NextRequest } from 'next/server';
import { POST } from './route';

const mockFetch = jest.fn();

describe('AVL deactivate route', () => {
  const originalFetch = global.fetch;
  const request = () =>
    new NextRequest('http://publish.localhost:3000/api/next/avl/archive?orgId=1&datasetId=2', {
      method: 'POST',
      headers: { cookie: 'sessionid=abc; csrftoken=tok' },
    });

  beforeEach(() => {
    mockFetch.mockReset();
    global.fetch = mockFetch as unknown as typeof fetch;
  });

  afterAll(() => {
    global.fetch = originalFetch;
  });

  it('returns the public path of the Django success redirect', async () => {
    mockFetch.mockResolvedValue(
      new Response(null, {
        status: 302,
        headers: { location: 'http://publish.localhost:8000/org/1/dataset/avl/2/deactivate/success' },
      }),
    );

    const response = await POST(request());

    expect(new URL(mockFetch.mock.calls[0][0]).pathname).toBe('/org/1/dataset/avl/2/deactivate/');
    expect(await response.json()).toEqual({ redirect: '/org/1/dataset/avl/2/deactivate/success' });
  });

  it('falls back to the public success path when Django does not redirect', async () => {
    mockFetch.mockResolvedValue(new Response('ok', { status: 200 }));

    const response = await POST(request());

    expect(await response.json()).toEqual({ redirect: '/org/1/dataset/avl/2/deactivate/success' });
  });
});
