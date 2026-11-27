/**
 * @jest-environment jsdom
 */

import {
  installSessionActivityFetchWatcher,
  reportSessionActivity,
  subscribeToSessionActivity,
} from './session-activity';

describe('reportSessionActivity', () => {
  const listener = jest.fn();
  let unsubscribe: () => void;

  beforeEach(() => {
    listener.mockClear();
    unsubscribe = subscribeToSessionActivity(listener);
  });

  afterEach(() => unsubscribe());

  it.each([200, 201, 204, 302, 400, 403, 404, 500])(
    'notifies for %i, which Django served with the session',
    (status) => {
      reportSessionActivity(status);

      expect(listener).toHaveBeenCalledTimes(1);
    },
  );

  it.each([401, 502, 503, 504])('does not notify for %i, which did not extend the session', (status) => {
    reportSessionActivity(status);

    expect(listener).not.toHaveBeenCalled();
  });
});

describe('installSessionActivityFetchWatcher', () => {
  const originalFetch = window.fetch;
  const fetchMock = jest.fn();
  const listener = jest.fn();
  let unsubscribe: () => void;
  let uninstall: () => void;

  const response = (status: number) => ({ status }) as Response;
  // jsdom has no Request; the watcher only reads `url` from it.
  const request = (url: string) => ({ url }) as Request;

  beforeEach(() => {
    jest.clearAllMocks();
    fetchMock.mockResolvedValue(response(200));
    window.fetch = fetchMock;
    unsubscribe = subscribeToSessionActivity(listener);
    uninstall = installSessionActivityFetchWatcher();
  });

  afterEach(() => {
    uninstall();
    unsubscribe();
    window.fetch = originalFetch;
  });

  it('reports the status of a same-origin /api/ request, relative or absolute', async () => {
    await window.fetch('/api/v1/things/');
    await window.fetch(`${window.location.origin}/api/auth/user/`);

    expect(listener).toHaveBeenCalledTimes(2);
  });

  it('reports non-401 error statuses but ignores 401 and gateway failures', async () => {
    for (const status of [404, 500, 401, 502, 503, 504]) {
      fetchMock.mockResolvedValueOnce(response(status));
      await window.fetch('/api/v1/things/');
    }

    expect(listener).toHaveBeenCalledTimes(2);
  });

  it('handles URL and Request inputs', async () => {
    await window.fetch(new URL('/api/v1/things/', window.location.origin));
    await window.fetch(request(`${window.location.origin}/api/v1/things/`));

    expect(listener).toHaveBeenCalledTimes(2);

    await window.fetch(new URL('https://elsewhere.example/api/v1/things/'));
    await window.fetch(request('https://elsewhere.example/api/v1/things/'));

    expect(listener).toHaveBeenCalledTimes(2);
  });

  it('ignores cross-origin requests', async () => {
    await window.fetch('https://elsewhere.example/api/v1/things/');
    await window.fetch('//elsewhere.example/api/v1/things/');

    expect(listener).not.toHaveBeenCalled();
  });

  it('ignores same-origin paths outside /api/', async () => {
    await window.fetch('/browse/');
    await window.fetch('/apiary/');
    await window.fetch('/_next/static/chunk.js');

    expect(listener).not.toHaveBeenCalled();
  });

  it('ignores /api/mapbox-token, which Next.js answers without Django', async () => {
    await window.fetch('/api/mapbox-token');
    await window.fetch('/api/mapbox-token?x=1');

    expect(listener).not.toHaveBeenCalled();
  });

  it('passes the arguments and the very same response through', async () => {
    const result = response(200);
    fetchMock.mockResolvedValueOnce(result);
    const init = { method: 'POST' };

    await expect(window.fetch('/api/v1/things/', init)).resolves.toBe(result);

    expect(fetchMock).toHaveBeenCalledWith('/api/v1/things/', init);
  });

  it('propagates a rejected fetch without reporting', async () => {
    const failure = new TypeError('Failed to fetch');
    fetchMock.mockRejectedValueOnce(failure);

    await expect(window.fetch('/api/v1/things/')).rejects.toBe(failure);

    expect(listener).not.toHaveBeenCalled();
  });

  it('restores the original fetch on uninstall', async () => {
    expect(window.fetch).not.toBe(fetchMock);

    uninstall();

    expect(window.fetch).toBe(fetchMock);
    await window.fetch('/api/v1/things/');
    expect(listener).not.toHaveBeenCalled();
  });

  it('wraps fetch once when installed twice and restores after the last uninstall', async () => {
    const uninstallAgain = installSessionActivityFetchWatcher();

    await window.fetch('/api/v1/things/');
    expect(listener).toHaveBeenCalledTimes(1);

    uninstall();
    expect(window.fetch).not.toBe(fetchMock);
    await window.fetch('/api/v1/things/');
    expect(listener).toHaveBeenCalledTimes(2);

    uninstallAgain();
    expect(window.fetch).toBe(fetchMock);
  });

  it('does not clobber a fetch that was replaced after install', () => {
    const replacement = jest.fn();
    window.fetch = replacement;

    uninstall();

    expect(window.fetch).toBe(replacement);
  });
});
