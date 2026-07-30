import type { NextRequest } from 'next/server';
import {
  djangoPath,
  forwardToDjango,
  getDjangoNamespace,
} from './django-gateway';

describe('getDjangoNamespace', () => {
  it('maps each public namespace to its Django host and upstream prefix', () => {
    expect(getDjangoNamespace('auth')).toEqual({
      upstreamPrefix: '/api/auth/',
      upstreamHost: 'localhost:8000',
    });
    expect(getDjangoNamespace('data')).toEqual({
      upstreamPrefix: '/api/',
      upstreamHost: 'data.localhost:8000',
    });
    expect(getDjangoNamespace('publish')).toEqual({
      upstreamPrefix: '/api/',
      upstreamHost: 'publish.localhost:8000',
    });
    expect(getDjangoNamespace('unknown')).toBeNull();
  });
});

describe('djangoPath', () => {
  it('preserves a trailing slash and encodes decoded path segments', () => {
    expect(
      djangoPath('/api/', ['v1', 'dataset name'], '/api/data/v1/dataset%20name/'),
    ).toBe('/api/v1/dataset%20name/');
  });
});

describe('forwardToDjango', () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    jest.clearAllMocks();
  });

  it('forwards a data request to internal Django with its host, query, and session', async () => {
    const upstreamResponse = { status: 200 } as Response;
    global.fetch = jest.fn().mockResolvedValue(upstreamResponse);
    const request = {
      method: 'GET',
      nextUrl: new URL('http://localhost:3000/api/data/v1/dataset/?limit=1'),
      headers: new Headers({ cookie: 'sessionid=session-value' }),
      arrayBuffer: jest.fn(),
    } as unknown as NextRequest;

    const response = await forwardToDjango(
      request,
      '/api/v1/dataset/',
      'data.localhost:8000',
    );

    expect(response).toBe(upstreamResponse);
    expect(global.fetch).toHaveBeenCalledWith(
      new URL('http://localhost:8000/api/v1/dataset/?limit=1'),
      expect.objectContaining({
        method: 'GET',
        redirect: 'manual',
        body: undefined,
      }),
    );
    const init = (global.fetch as jest.Mock).mock.calls[0][1] as RequestInit;
    const headers = new Headers(init.headers);
    expect(headers.get('host')).toBe('data.localhost:8000');
    expect(headers.get('cookie')).toBe('sessionid=session-value');
  });

  it('forwards a mutation body and CSRF header without the incoming content length', async () => {
    const body = new ArrayBuffer(18);
    global.fetch = jest.fn().mockResolvedValue({ status: 204 } as Response);
    const request = {
      method: 'PATCH',
      nextUrl: new URL('http://localhost:3000/api/publish/fares/1/'),
      headers: new Headers({
        'content-length': String(body.byteLength),
        'content-type': 'application/json',
        'x-csrftoken': 'csrf-value',
      }),
      arrayBuffer: jest.fn().mockResolvedValue(body),
    } as unknown as NextRequest;

    await forwardToDjango(request, '/api/fares/1/', 'publish.localhost:8000');

    const init = (global.fetch as jest.Mock).mock.calls[0][1] as RequestInit;
    const headers = new Headers(init.headers);
    expect(init.body).toBe(body);
    expect(headers.get('host')).toBe('publish.localhost:8000');
    expect(headers.get('x-csrftoken')).toBe('csrf-value');
    expect(headers.has('content-length')).toBe(false);
  });
});