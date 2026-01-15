/**
 * Logout Page
 * 
 * Handles user logout
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';

export default function LogoutPage() {
  const { signOut, isAuthenticated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated) {
      signOut().then(() => {
        router.push('/');
        router.refresh();
      });
    } else {
      router.push('/');
    }
  }, [isAuthenticated, signOut, router]);

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Signing out...</h1>
            <p className="govuk-body">Please wait while we sign you out.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

