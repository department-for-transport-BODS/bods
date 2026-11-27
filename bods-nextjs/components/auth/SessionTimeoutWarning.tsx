/**
 * Session Timeout Warning
 *
 * Port of Django's transit_odp/templates/snippets/timeout_warning_modal.html and
 * transit_odp/frontend/assets/js/timeout-warning.js. Warns signed-in users 30s
 * before their session expires and reloads the page when it does.
 *
 * Deviation from Django: Django restarts the countdown on every full page load.
 * Navigation here is client-side, so the countdown restarts whenever a Django
 * request succeeds (see lib/session-activity.ts) and when "Refresh session" is used.
 */

'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { api } from '@/lib/api-client';
import { reloadPage } from '@/lib/reload-page';
import {
  installSessionActivityFetchWatcher,
  subscribeToSessionActivity,
} from '@/lib/session-activity';

const WARNING_WINDOW_SECONDS = 30;
// Cheap authenticated endpoint; any Django request extends the session.
const REFRESH_SESSION_ENDPOINT = '/api/auth/user/';

const INITIAL_MESSAGE = 'Your session will expire soon. Click Refresh session for more time.';

function countdownMessage(secondsLeft: number): string {
  return `Your session will expire in ${secondsLeft} seconds. Click Refresh session for more time.`;
}

export function SessionTimeoutWarning() {
  const { isAuthenticated, user } = useAuth();
  const sessionAge = user?.session_cookie_age;

  if (!isAuthenticated || !sessionAge) {
    return null;
  }

  return <TimeoutWarningDialog sessionAge={sessionAge} />;
}

function TimeoutWarningDialog({ sessionAge }: { sessionAge: number }) {
  const [isOpen, setIsOpen] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState<number | null>(null);
  const dialogRef = useRef<HTMLDivElement>(null);
  const messageIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  const stopCountdown = useCallback(() => {
    if (messageIntervalRef.current !== null) {
      clearInterval(messageIntervalRef.current);
      messageIntervalRef.current = null;
    }
  }, []);

  const closeDialog = useCallback(() => {
    stopCountdown();
    document.body.classList.remove('disable-scroll');
    setSecondsLeft(null);
    setIsOpen(false);
    previousFocusRef.current?.focus();
    previousFocusRef.current = null;
  }, [stopCountdown]);

  useEffect(() => {
    let openTimer: ReturnType<typeof setTimeout>;
    let reloadTimer: ReturnType<typeof setTimeout>;
    // Timers stall while the machine sleeps, so expiry is judged against the wall clock.
    let expiresAt = 0;
    const hasExpired = () => Date.now() >= expiresAt;

    const openDialog = () => {
      let counter = WARNING_WINDOW_SECONDS;
      stopCountdown();
      messageIntervalRef.current = setInterval(() => {
        setSecondsLeft(counter);
        counter -= 1;
      }, 1000);

      document.body.classList.add('disable-scroll');
      previousFocusRef.current =
        document.activeElement instanceof HTMLElement ? document.activeElement : null;
      setIsOpen(true);
    };

    const startTimers = () => {
      expiresAt = Date.now() + sessionAge * 1000;
      openTimer = setTimeout(openDialog, Math.max(sessionAge - WARNING_WINDOW_SECONDS, 0) * 1000);
      reloadTimer = setTimeout(reloadPage, sessionAge * 1000);
    };

    // The session was just extended, so the countdown starts again and any
    // warning already showing no longer applies. Past expiry, the response came
    // from an anonymous request and extended nothing.
    const restart = () => {
      if (hasExpired()) {
        reloadPage();
        return;
      }
      clearTimeout(openTimer);
      clearTimeout(reloadTimer);
      closeDialog();
      startTimers();
    };

    const reloadIfExpired = () => {
      if (document.visibilityState === 'visible' && hasExpired()) {
        reloadPage();
      }
    };

    startTimers();
    const unsubscribe = subscribeToSessionActivity(restart);
    document.addEventListener('visibilitychange', reloadIfExpired);

    return () => {
      unsubscribe();
      document.removeEventListener('visibilitychange', reloadIfExpired);
      clearTimeout(openTimer);
      clearTimeout(reloadTimer);
      stopCountdown();
      document.body.classList.remove('disable-scroll');
    };
  }, [sessionAge, closeDialog, stopCountdown]);

  // Only signed-in users have a session to keep alive, and this dialog only renders for them.
  useEffect(() => installSessionActivityFetchWatcher(), []);

  useEffect(() => {
    if (isOpen) {
      dialogRef.current?.focus();
    }
  }, [isOpen]);

  // Any successful request restarts the countdown (the activity subscription above),
  // including this one, which also closes the dialog. If it fails the dialog stays open.
  const refreshSession = useCallback(() => {
    api.get(REFRESH_SESSION_ENDPOINT, { cache: 'no-store' }).catch(() => undefined);
  }, []);

  return (
    <>
      <div id="dialog-overlay" style={{ display: isOpen ? 'block' : 'none' }}></div>
      <div
        ref={dialogRef}
        className="govuk-timeout-warning dialog"
        role="dialog"
        aria-live="polite"
        aria-labelledby="dialog-title"
        tabIndex={-1}
        style={{ display: isOpen ? 'block' : 'none' }}
      >
        <h1 id="dialog-title" className="govuk-heading-l">
          Timeout warning
        </h1>
        <p className="govuk-body">
          {secondsLeft === null ? INITIAL_MESSAGE : countdownMessage(secondsLeft)}
        </p>
        <button type="button" className="govuk-button dialog-refresh" onClick={refreshSession}>
          Refresh session
        </button>
        {/* Django's markup has whitespace between the buttons, which renders as a gap. */}
        {' '}
        <button
          type="button"
          className="govuk-button govuk-button--secondary dialog-cancel"
          onClick={closeDialog}
        >
          Ignore
        </button>
      </div>
    </>
  );
}
