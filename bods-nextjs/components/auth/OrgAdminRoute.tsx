/**
 * Org Admin Route Component
 *
 * Wraps pages whose actions are restricted to organisation admins, matching the
 * checks the account management APIs apply. This
 * keeps admin-only UI from rendering for users who cannot act on it.
 */

'use client';

import { useRouter } from 'next/navigation';
import { useEffect, type ReactNode } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { ProtectedRoute } from './ProtectedRoute';

function RequireOrgAdmin({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const router = useRouter();
  const isOrgAdmin = Boolean(user?.is_org_admin && user.organisation_id);

  useEffect(() => {
    if (!user || isOrgAdmin) {
      return;
    }

    router.replace('/account');
  }, [user, isOrgAdmin, router]);

  if (!isOrgAdmin) {
    return null;
  }

  return <>{children}</>;
}

export function OrgAdminRoute({ children }: { children: ReactNode }) {
  return (
    <ProtectedRoute>
      <RequireOrgAdmin>{children}</RequireOrgAdmin>
    </ProtectedRoute>
  );
}
