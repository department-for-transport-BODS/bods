/**
 * @jest-environment jsdom
 */

import { act, fireEvent, render, screen } from '@testing-library/react';
import { SessionTimeoutWarning } from './SessionTimeoutWarning';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/lib/api-client';
import { reloadPage } from '@/lib/reload-page';
import { reportSessionActivity } from '@/lib/session-activity';

jest.mock('@/hooks/useAuth', () => ({ useAuth: jest.fn() }));
jest.mock('@/lib/api-client', () => ({ api: { get: jest.fn() } }));
jest.mock('@/lib/reload-page', () => ({ reloadPage: jest.fn() }));

const SESSION_AGE = 600;
const WARNING_WINDOW = 30;

function signedIn(sessionCookieAge = SESSION_AGE) {
  (useAuth as jest.Mock).mockReturnValue({
    isAuthenticated: true,
    user: { id: 1, email: 'user@example.com', session_cookie_age: sessionCookieAge },
  });
}

function advance(seconds: number) {
  act(() => {
    jest.advanceTimersByTime(seconds * 1000);
  });
}

const dialog = () => screen.getByRole('dialog', { hidden: true });
const isOpen = () => dialog().style.display === 'block';

beforeEach(() => {
  jest.useFakeTimers();
  jest.clearAllMocks();
  (api.get as jest.Mock).mockResolvedValue({});
  signedIn();
});

afterEach(() => {
  jest.useRealTimers();
});

describe('SessionTimeoutWarning', () => {
  it('renders Django’s markup and copy, hidden until the warning window', () => {
    render(<SessionTimeoutWarning />);

    expect(dialog()).toHaveClass('govuk-timeout-warning', 'dialog');
    expect(dialog()).toHaveAttribute('aria-live', 'polite');
    expect(screen.getByRole('heading', { name: 'Timeout warning', hidden: true })).toHaveClass(
      'govuk-heading-l',
    );
    expect(
      screen.getByText('Your session will expire soon. Click Refresh session for more time.'),
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Refresh session', hidden: true })).toHaveClass(
      'govuk-button',
      'dialog-refresh',
    );
    expect(screen.getByRole('button', { name: 'Ignore', hidden: true })).toHaveClass(
      'govuk-button',
      'govuk-button--secondary',
      'dialog-cancel',
    );
    expect(isOpen()).toBe(false);
    expect(document.getElementById('dialog-overlay')).toHaveStyle({ display: 'none' });
  });

  it('opens 30 seconds before the session expires, locking page scroll and taking focus', () => {
    render(<SessionTimeoutWarning />);

    advance(SESSION_AGE - WARNING_WINDOW - 1);
    expect(isOpen()).toBe(false);

    advance(1);
    expect(isOpen()).toBe(true);
    expect(document.getElementById('dialog-overlay')).toHaveStyle({ display: 'block' });
    expect(document.body).toHaveClass('disable-scroll');
    expect(dialog()).toHaveFocus();
  });

  it('counts down every second from 30', () => {
    render(<SessionTimeoutWarning />);
    advance(SESSION_AGE - WARNING_WINDOW);

    advance(1);
    expect(
      screen.getByText('Your session will expire in 30 seconds. Click Refresh session for more time.'),
    ).toBeInTheDocument();

    advance(1);
    expect(
      screen.getByText('Your session will expire in 29 seconds. Click Refresh session for more time.'),
    ).toBeInTheDocument();

    advance(28);
    expect(
      screen.getByText('Your session will expire in 1 seconds. Click Refresh session for more time.'),
    ).toBeInTheDocument();
  });

  it('Refresh session calls the current-user endpoint, restarts the countdown and closes', async () => {
    // The real api client fetches through window.fetch, whose watcher reports the activity;
    // mirror that here.
    (api.get as jest.Mock).mockImplementation(async () => {
      reportSessionActivity(200);
      return {};
    });
    render(<SessionTimeoutWarning />);
    advance(SESSION_AGE - WARNING_WINDOW + 5);
    expect(isOpen()).toBe(true);

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Refresh session', hidden: true }));
    });

    expect(api.get).toHaveBeenCalledWith('/api/auth/user/', expect.objectContaining({ cache: 'no-store' }));
    expect(isOpen()).toBe(false);
    expect(document.body).not.toHaveClass('disable-scroll');
    expect(screen.getByText(/Your session will expire soon/)).toBeInTheDocument();

    // Old timers are gone: neither a reload at the original age nor an early warning.
    advance(WARNING_WINDOW);
    expect(reloadPage).not.toHaveBeenCalled();
    advance(SESSION_AGE - WARNING_WINDOW * 2 - 5);
    expect(isOpen()).toBe(false);

    // The warning opens again a full cycle after the refresh.
    advance(WARNING_WINDOW);
    expect(isOpen()).toBe(true);
  });

  it('keeps the dialog open when Refresh session fails', async () => {
    (api.get as jest.Mock).mockRejectedValue(new Error('boom'));
    render(<SessionTimeoutWarning />);
    advance(SESSION_AGE - WARNING_WINDOW);

    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Refresh session', hidden: true }));
    });

    expect(isOpen()).toBe(true);
  });

  it('Ignore closes the dialog but the session still reloads at expiry', () => {
    render(<SessionTimeoutWarning />);
    advance(SESSION_AGE - WARNING_WINDOW + 3);

    fireEvent.click(screen.getByRole('button', { name: 'Ignore', hidden: true }));

    expect(isOpen()).toBe(false);
    expect(document.body).not.toHaveClass('disable-scroll');

    // The countdown no longer ticks, and the dialog stays shut.
    advance(WARNING_WINDOW - 4);
    expect(isOpen()).toBe(false);
    expect(reloadPage).not.toHaveBeenCalled();

    advance(1);
    expect(reloadPage).toHaveBeenCalledTimes(1);
  });

  it('reloads the page when the session expires', () => {
    render(<SessionTimeoutWarning />);

    advance(SESSION_AGE - 1);
    expect(reloadPage).not.toHaveBeenCalled();

    advance(1);
    expect(reloadPage).toHaveBeenCalledTimes(1);
  });

  it('uses the session age from the current user, not a fixed value', () => {
    signedIn(120);
    render(<SessionTimeoutWarning />);

    advance(120 - WARNING_WINDOW);
    expect(isOpen()).toBe(true);
    advance(WARNING_WINDOW);
    expect(reloadPage).toHaveBeenCalledTimes(1);
  });

  it('restarts the countdown when a Django request succeeds', () => {
    render(<SessionTimeoutWarning />);
    advance(SESSION_AGE - WARNING_WINDOW - 10);

    act(() => reportSessionActivity(200));

    advance(WARNING_WINDOW + 10);
    expect(isOpen()).toBe(false);
    advance(SESSION_AGE - WARNING_WINDOW * 2 - 10 - 1);
    expect(isOpen()).toBe(false);
    advance(1);
    expect(isOpen()).toBe(true);

    advance(WARNING_WINDOW);
    expect(reloadPage).toHaveBeenCalledTimes(1);
  });

  it('restarts the countdown for error responses other than 401', () => {
    render(<SessionTimeoutWarning />);
    advance(SESSION_AGE - WARNING_WINDOW - 10);

    act(() => reportSessionActivity(403));

    advance(WARNING_WINDOW + 10);
    expect(isOpen()).toBe(false);
  });

  it('does not restart the countdown on a 401', () => {
    render(<SessionTimeoutWarning />);
    advance(SESSION_AGE - WARNING_WINDOW - 10);

    act(() => reportSessionActivity(401));

    advance(10);
    expect(isOpen()).toBe(true);
    advance(WARNING_WINDOW);
    expect(reloadPage).toHaveBeenCalledTimes(1);
  });

  it('reloads instead of restarting when activity arrives after the session has expired', () => {
    render(<SessionTimeoutWarning />);
    // Timers do not fire while the machine sleeps, but the wall clock moves on.
    jest.setSystemTime(Date.now() + SESSION_AGE * 1000);

    act(() => reportSessionActivity(200));

    expect(reloadPage).toHaveBeenCalledTimes(1);
  });

  it('reloads when the page becomes visible after the session has expired', () => {
    render(<SessionTimeoutWarning />);
    const becomeVisible = () => act(() => document.dispatchEvent(new Event('visibilitychange')));

    becomeVisible();
    expect(reloadPage).not.toHaveBeenCalled();

    jest.setSystemTime(Date.now() + SESSION_AGE * 1000);
    becomeVisible();
    expect(reloadPage).toHaveBeenCalledTimes(1);
  });

  it('closes an open warning when a request shows the session was extended', () => {
    render(<SessionTimeoutWarning />);
    advance(SESSION_AGE - WARNING_WINDOW + 2);
    expect(isOpen()).toBe(true);

    act(() => reportSessionActivity(200));

    expect(isOpen()).toBe(false);
    expect(document.body).not.toHaveClass('disable-scroll');
  });

  describe('fetch watcher', () => {
    const originalFetch = window.fetch;
    const fetchMock = jest.fn();

    beforeEach(() => {
      fetchMock.mockReset().mockResolvedValue({ status: 200 });
      window.fetch = fetchMock;
    });

    afterEach(() => {
      window.fetch = originalFetch;
    });

    it('restarts the countdown when a raw same-origin /api/ fetch succeeds', async () => {
      render(<SessionTimeoutWarning />);
      advance(SESSION_AGE - WARNING_WINDOW - 1);

      await act(async () => {
        await window.fetch('/api/v1/anything/');
      });

      advance(WARNING_WINDOW + 1);
      expect(isOpen()).toBe(false);
      advance(SESSION_AGE - WARNING_WINDOW);
      expect(isOpen()).toBe(true);
    });

    it('restores window.fetch on unmount', () => {
      const { unmount } = render(<SessionTimeoutWarning />);
      expect(window.fetch).not.toBe(fetchMock);

      unmount();

      expect(window.fetch).toBe(fetchMock);
    });

    it('does not wrap window.fetch when signed out', () => {
      (useAuth as jest.Mock).mockReturnValue({ isAuthenticated: false, user: null });

      render(<SessionTimeoutWarning />);

      expect(window.fetch).toBe(fetchMock);
    });
  });

  it('renders nothing when signed out', () => {
    (useAuth as jest.Mock).mockReturnValue({ isAuthenticated: false, user: null });

    const { container } = render(<SessionTimeoutWarning />);

    expect(container).toBeEmptyDOMElement();
    advance(SESSION_AGE);
    expect(reloadPage).not.toHaveBeenCalled();
  });

  it('renders nothing when the session age is unknown', () => {
    (useAuth as jest.Mock).mockReturnValue({
      isAuthenticated: true,
      user: { id: 1, email: 'user@example.com' },
    });
    const { container } = render(<SessionTimeoutWarning />);

    expect(container).toBeEmptyDOMElement();
  });

  it('stops all timers, the countdown and the scroll lock when the user signs out', () => {
    const { rerender, container } = render(<SessionTimeoutWarning />);
    advance(SESSION_AGE - WARNING_WINDOW + 2);
    expect(document.body).toHaveClass('disable-scroll');

    (useAuth as jest.Mock).mockReturnValue({ isAuthenticated: false, user: null });
    rerender(<SessionTimeoutWarning />);

    expect(container).toBeEmptyDOMElement();
    expect(document.body).not.toHaveClass('disable-scroll');
    advance(SESSION_AGE);
    expect(reloadPage).not.toHaveBeenCalled();
    expect(jest.getTimerCount()).toBe(0);
  });

  it('stops all timers on unmount', () => {
    const { unmount } = render(<SessionTimeoutWarning />);
    advance(SESSION_AGE - WARNING_WINDOW + 2);

    unmount();

    expect(jest.getTimerCount()).toBe(0);
    expect(document.body).not.toHaveClass('disable-scroll');
    advance(SESSION_AGE);
    expect(reloadPage).not.toHaveBeenCalled();
  });
});
