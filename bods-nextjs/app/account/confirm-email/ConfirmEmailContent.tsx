/**
 * Confirm Email Content Component
 *
 * Confirms the address behind a verification key, mirroring Django's
 * ConfirmEmailView with ACCOUNT_CONFIRM_EMAIL_ON_GET. A valid key confirms
 * and redirects to login. An invalid or already-used key stays here with
 * the expired copy from email_confirm.html.
 */

'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api-client';
import { ErrorSummary } from '@/components/shared';

interface ConfirmEmailContentProps {
  confirmationKey: string;
}

export function ConfirmEmailContent({ confirmationKey }: ConfirmEmailContentProps) {
  const router = useRouter();
  const [status, setStatus] = useState<'loading' | 'error'>('loading');

  useEffect(() => {
    let isCancelled = false;

    api
      .post('/api/auth/confirm-email/', { key: confirmationKey })
      .then(() => {
        if (!isCancelled) {
          router.replace('/account/login');
        }
      })
      .catch(() => {
        if (!isCancelled) setStatus('error');
      });

    return () => {
      isCancelled = true;
    };
  }, [confirmationKey, router]);

  if (status === 'loading') {
    return null;
  }

  return (
    <>
      <h1 className="govuk-heading-xl">Confirm email address</h1>
      <ErrorSummary
        title="This email confirmation link expired or is invalid."
        errors={[{ text: 'Issue a new email confirmation request', href: '/account/login' }]}
      />
    </>
  );
}
