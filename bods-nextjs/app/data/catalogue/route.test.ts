/** @jest-environment node */

import { NextRequest } from 'next/server';
import { GET } from './route';
import { forwardToDjango } from '@/lib/django-gateway';
import { DJANGO_HOSTS } from '@/config/server';

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

  it('requests a signed download URL from the Django www API', async () => {
    mockForward.mockResolvedValue(
      Response.json({ url: 'https://cdn.example.test/data-catalogue/catalogue.zip' }),
    );

    const response = await GET(request);

    expect(mockForward).toHaveBeenCalledWith(
      request,
      '/api/catalogue/',
      new URL(DJANGO_HOSTS.www).host,
    );
    expect(response.status).toBe(302);
    expect(response.headers.get('Location')).toBe(
      'https://cdn.example.test/data-catalogue/catalogue.zip',
    );
  });

  it('returns a gateway error when the API does not provide an HTTPS URL', async () => {
    mockForward.mockResolvedValue(Response.json({ url: 'http://example.test/file.zip' }));

    const response = await GET(request);

    expect(response.status).toBe(502);
  });

  it('renders the 404 page when no catalogue has been uploaded', async () => {
    mockForward.mockResolvedValue(new Response('Not found', { status: 404 }));

    await expect(GET(request)).rejects.toThrow('NEXT_HTTP_ERROR_FALLBACK;404');
  });
});
