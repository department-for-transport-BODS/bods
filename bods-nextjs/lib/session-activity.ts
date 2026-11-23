/**
 * Session activity signal.
 *
 * Django (SESSION_SAVE_EVERY_REQUEST) extends the session on every request it
 * serves, and the legacy timeout warning restarts its countdown on each full page
 * load. The Next.js app navigates client-side, so a window.fetch watcher reports
 * each response Django served here and the session timeout warning restarts its
 * countdown from it.
 */

type SessionActivityListener = () => void;

const listeners = new Set<SessionActivityListener>();

/** Returns an unsubscribe function. */
export function subscribeToSessionActivity(listener: SessionActivityListener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

// Gateway statuses: Django never returns these, so they mean the request did
// not reach it (or was not answered) and the session was not extended.
const GATEWAY_FAILURE_STATUSES = new Set([502, 503, 504]);

/**
 * Call with the status of every response received from a same-origin request
 * that Next.js hands to Django (`/api/...`). A 401 means the session was not
 * valid, and a gateway failure means Django did not serve the request, so
 * neither extends anything.
 */
export function reportSessionActivity(status: number): void {
  if (status === 401 || GATEWAY_FAILURE_STATUSES.has(status)) {
    return;
  }
  for (const listener of Array.from(listeners)) {
    listener();
  }
}

// Next.js answers this itself and never forwards it to Django.
const NEXT_ONLY_API_PATHS = ['/api/mapbox-token'];

function isDjangoApiRequest(input: RequestInfo | URL): boolean {
  let url: URL;
  try {
    const raw = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
    url = new URL(raw, window.location.href);
  } catch {
    return false;
  }
  if (url.origin !== window.location.origin || !url.pathname.startsWith('/api/')) {
    return false;
  }
  return !NEXT_ONLY_API_PATHS.some(
    (path) => url.pathname === path || url.pathname.startsWith(`${path}/`),
  );
}

let installCount = 0;
let originalFetch: typeof window.fetch | null = null;
let watchingFetch: typeof window.fetch | null = null;

/**
 * Wraps window.fetch so every response to a same-origin `/api/...` request
 * (which Next.js hands to Django) is reported with `reportSessionActivity`,
 * wherever in the app the fetch is made. The response and any rejection pass
 * through untouched. Installs are reference counted, so a repeated install
 * (e.g. React StrictMode) wraps fetch once. Returns an uninstall function that
 * restores the original fetch once the last install is removed.
 */
export function installSessionActivityFetchWatcher(): () => void {
  if (installCount === 0) {
    const original = window.fetch;
    const watching: typeof window.fetch = (input, init) =>
      original.call(window, input, init).then((response) => {
        if (isDjangoApiRequest(input)) {
          reportSessionActivity(response.status);
        }
        return response;
      });
    originalFetch = original;
    watchingFetch = watching;
    window.fetch = watching;
  }
  installCount += 1;

  let uninstalled = false;
  return () => {
    if (uninstalled) {
      return;
    }
    uninstalled = true;
    installCount -= 1;
    if (installCount === 0) {
      // Leave fetch alone if something else has replaced it since.
      if (window.fetch === watchingFetch && originalFetch) {
        window.fetch = originalFetch;
      }
      originalFetch = null;
      watchingFetch = null;
    }
  };
}
