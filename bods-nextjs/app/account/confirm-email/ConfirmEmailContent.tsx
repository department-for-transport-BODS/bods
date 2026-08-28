/**
 * Confirm Email Content Component
 *
 * Confirms the address behind a verification key, mirroring Django's
 * ConfirmEmailView, which confirms as soon as the link is opened.
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api-client';
import { ErrorSummary } from '@/components/shared';

const REDIRECT_DELAY_MS = 3000;

interface ConfirmEmailContentProps {
  confirmationKey: string;
}

export function ConfirmEmailContent({ confirmationKey }: ConfirmEmailContentProps) {
  const router = useRouter();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');

  useEffect(() => {
    let isCancelled = false;

    api
      .post('/api/auth/confirm-email/', { key: confirmationKey })
      .then(() => {
        if (!isCancelled) setStatus('success');
      })
      .catch(() => {
        if (!isCancelled) setStatus('error');
      });

    return () => {
      isCancelled = true;
    };
  }, [confirmationKey]);

  useEffect(() => {
    if (status !== 'success') {
      return;
    }

    const timer = setTimeout(() => router.push('/account/login'), REDIRECT_DELAY_MS);
    return () => clearTimeout(timer);
  }, [status, router]);

  if (status === 'loading') {
    return <p className="govuk-body">Confirming your email address...</p>;
  }

  if (status === 'success') {
    return (
      <div className="govuk-panel govuk-panel--confirmation">
        <h2 className="govuk-panel__title">Email confirmed</h2>
        <div className="govuk-panel__body">
          Your email has been confirmed. You can now sign in.
        </div>
      </div>
    );
  }

  return (
    <ErrorSummary
      title="This email confirmation link expired or is invalid."
      errors={[{ text: 'Issue a new email confirmation request', href: '/account/login' }]}
    />
  );
}
