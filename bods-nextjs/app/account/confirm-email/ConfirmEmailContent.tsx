/**
 * Confirm Email Content Component
 * 
 * NextJS component to run in the browser to handle the user clicking a 
 * link to trigger an email to be sent to confirm their email address
 */

'use client';

import { useEffect, useState } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api-client';

export function ConfirmEmailContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const key = searchParams.get('key');
    if (!key) {
      setStatus('error');
      setMessage('Invalid confirmation link');
      return;
    }

    api.post('/api/auth/confirm-email/', { key })
      .then(() => {
        setStatus('success');
        setMessage('Your email has been confirmed. You can now sign in.');
        setTimeout(() => {
          router.push('/account/login');
        }, 3000);
      })
      .catch(() => {
        setStatus('error');
        setMessage('Invalid or expired confirmation link.');
      });
  }, [searchParams, router]);

  if (status === 'loading') {
    return <p className="govuk-body">Confirming your email address...</p>;
  }

  if (status === 'success') {
    return (
      <div className="govuk-panel govuk-panel--confirmation">
        <h2 className="govuk-panel__title">Email confirmed</h2>
        <div className="govuk-panel__body">
          {message}
        </div>
      </div>
    );
  }

  return (
    <div className="govuk-error-summary" role="alert">
      <h2 className="govuk-error-summary__title">
        Confirmation failed
      </h2>
      <div className="govuk-error-summary__body">
        <p className="govuk-body">{message}</p>
      </div>
    </div>
  );
}

