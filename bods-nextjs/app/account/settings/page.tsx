'use client';

/**
 * Account settings
 *
 * Mirrors Django's users/users_settings.html: username/email/api key display,
 * change password link, and (for org users) notification preferences.
 * Available on every service host, like login and password change.
 */

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { HOSTS, wwwPath } from '@/config/client';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorSummary } from '@/components/shared';
import { getCsrfToken } from '@/lib/api-client';

interface AccountSettings {
  username: string;
  email: string;
  apiKey: string;
  showNotificationsForm: boolean;
  showInvitationNotify: boolean;
  notifyInvitationAccepted: boolean;
  notifyAvlUnavailable: boolean;
  dailyComplianceCheckAlert: boolean;
}

function AccountSettingsContent() {
  const [settings, setSettings] = useState<AccountSettings | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    let isCancelled = false;

    fetch('/api/auth/settings/', { credentials: 'include' })
      .then((response) => response.json())
      .then((data: AccountSettings) => {
        if (!isCancelled) setSettings(data);
      })
      .catch(() => {
        if (!isCancelled) setError('Unable to load your account settings.');
      })
      .finally(() => {
        if (!isCancelled) setIsLoading(false);
      });

    return () => {
      isCancelled = true;
    };
  }, []);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!settings) return;

    setIsSaving(true);
    setError('');
    setSaved(false);

    try {
      const csrfToken = getCsrfToken();
      const response = await fetch('/api/auth/settings/update/', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({
          notify_invitation_accepted: settings.notifyInvitationAccepted,
          notify_avl_unavailable: settings.notifyAvlUnavailable,
          daily_compliance_check_alert: settings.dailyComplianceCheckAlert,
        }),
      });
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        setError(data.error || 'Unable to save your settings.');
        return;
      }

      setSaved(true);
    } catch {
      setError('Unable to save your settings.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <Breadcrumbs
          items={[
            { label: 'Bus Open Data Service', href: HOSTS.www },
            { label: 'Account settings', current: true },
          ]}
        />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Account settings</h1>
            <p className="govuk-body-l">Account details</p>

            {isLoading && <p className="govuk-body">Loading...</p>}
            {!isLoading && error && <ErrorSummary errors={[error]} summaryId="account-settings-error-title" />}

            {!isLoading && settings && (
              <>
                <table className="govuk-table manage-users-table">
                  <tbody className="govuk-table__body">
                    <tr className="govuk-table__row">
                      <td className="govuk-table__cell manage-users-table__key">User name</td>
                      <td colSpan={2} className="govuk-table__cell">{settings.username}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <td className="govuk-table__cell manage-users-table__key">Email address</td>
                      <td colSpan={2} className="govuk-table__cell">{settings.email}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <td className="govuk-table__cell manage-users-table__key">Password</td>
                      <td className="govuk-table__cell">●●●●●●●●</td>
                      <td className="govuk-table__cell">
                        <Link className="govuk-link" href="/account/password/change">Change</Link>
                      </td>
                    </tr>
                    <tr className="govuk-table__row">
                      <td className="govuk-table__cell manage-users-table__key">API Key</td>
                      <td colSpan={2} className="govuk-table__cell">{settings.apiKey}</td>
                    </tr>
                  </tbody>
                </table>

                {settings.showNotificationsForm && (
                  <form onSubmit={handleSubmit}>
                    <h3 className="govuk-heading-m">Notification settings</h3>
                    <span className="govuk-hint">
                      Choose what you would like to receive below. Allow up to 24 hours for any changes to take effect.
                    </span>

                    {saved && <p className="govuk-body">Your settings have been saved.</p>}

                    <div className="govuk-checkboxes__item">
                      <input
                        className="govuk-checkboxes__input"
                        id="notify_avl_unavailable"
                        type="checkbox"
                        checked={settings.notifyAvlUnavailable}
                        onChange={(e) => setSettings({ ...settings, notifyAvlUnavailable: e.target.checked })}
                      />
                      <label className="govuk-label govuk-checkboxes__label" htmlFor="notify_avl_unavailable">
                        No vehicle activity alert
                      </label>
                      <div className="govuk-hint govuk-checkboxes__hint">
                        Receive an email if data is not received from your AVL feed for more than 5 minutes
                      </div>
                    </div>

                    <div className="govuk-checkboxes__item">
                      <input
                        className="govuk-checkboxes__input"
                        id="daily_compliance_check_alert"
                        type="checkbox"
                        checked={settings.dailyComplianceCheckAlert}
                        onChange={(e) => setSettings({ ...settings, dailyComplianceCheckAlert: e.target.checked })}
                      />
                      <label className="govuk-label govuk-checkboxes__label" htmlFor="daily_compliance_check_alert">
                        Daily SIRI-VM compliance check alert
                      </label>
                      <div className="govuk-hint govuk-checkboxes__hint">
                        Receive an email every day once your AVL feed&apos;s compliance status has been re-calculated by
                        BODS. This ensures you&apos;re up to date on your feed&apos;s compliance.
                      </div>
                    </div>

                    {settings.showInvitationNotify && (
                      <div className="govuk-checkboxes__item">
                        <input
                          className="govuk-checkboxes__input"
                          id="notify_invitation_accepted"
                          type="checkbox"
                          checked={settings.notifyInvitationAccepted}
                          onChange={(e) => setSettings({ ...settings, notifyInvitationAccepted: e.target.checked })}
                        />
                        <label className="govuk-label govuk-checkboxes__label" htmlFor="notify_invitation_accepted">
                          Team members accept invitation
                        </label>
                      </div>
                    )}

                    <button type="submit" className="govuk-button govuk-!-margin-top-4" disabled={isSaving}>
                      {isSaving ? 'Saving...' : 'Save'}
                    </button>
                  </form>
                )}
              </>
            )}
          </div>

          <div className="govuk-grid-column-one-third">
            <h2 className="govuk-heading-m">Need help with operator data requirements?</h2>
            <ul className="govuk-list">
              <li>
                <Link className="govuk-link" href={wwwPath('/contact')}>Contact the Bus Open Data Service</Link>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AccountSettingsPage() {
  return (
    <ProtectedRoute>
      <AccountSettingsContent />
    </ProtectedRoute>
  );
}
