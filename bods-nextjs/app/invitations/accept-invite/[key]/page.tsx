'use client';

/**
 * Invitation accept page.
 *
 * Mirrors Django's invitations:accept-invite (AcceptInvite).
 * Valid keys stash the invite and redirect to /account/signup with no
 * intermediate copy. Expired or already-accepted keys render
 * invitation_expired.html at this URL. Keys that are not \w+ 404.
 */

import { useEffect, useState } from 'react';
import { notFound, useParams, useRouter } from 'next/navigation';
import { api, ApiError } from '@/lib/api-client';
import { wwwPath } from '@/config/client';

const DJANGO_INVITE_KEY = /^\w+$/;

export default function AcceptInvitePage() {
  const params = useParams();
  const router = useRouter();
  const key = String(params.key || '');
  const [isExpired, setIsExpired] = useState(false);
  const keyIsValid = DJANGO_INVITE_KEY.test(key);

  useEffect(() => {
    if (!keyIsValid) {
      return;
    }

    let isCancelled = false;

    api
      .post('/api/auth/invite/accept/', { key })
      .then(() => {
        if (!isCancelled) {
          router.replace('/account/signup');
        }
      })
      .catch((error: unknown) => {
        if (isCancelled) {
          return;
        }

        if (error instanceof ApiError && error.status === 410) {
          setIsExpired(true);
          return;
        }

        setIsExpired(true);
      });

    return () => {
      isCancelled = true;
    };
  }, [key, keyIsValid, router]);

  if (!keyIsValid) {
    return notFound();
  }

  if (!isExpired) {
    return null;
  }

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-full">
            <p className="govuk-body">
              This invitation link has already been accepted or has expired.
            </p>
            <p className="govuk-body">
              Please request a new invitation by asking your organisation admin to resend the
              invitation from the user management section, or by{' '}
              <a className="govuk-link" href={wwwPath('/contact')}>
                contacting us.
              </a>
            </p>
            <p className="govuk-body">
              Once a new invitation is sent please accept the invite within 72 hours of receiving
              it.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
