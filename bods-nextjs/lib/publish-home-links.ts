import { publishAppPath } from '@/config/client';
import type { User } from '@/types';

/** Mirrors transit_odp.users.constants.AccountType.abods_user. */
export const ABODS_USER_ACCOUNT_TYPE = 6;

export type PublishHomeUser = Pick<
  User,
  'account_type' | 'is_org_user' | 'is_agent_user' | 'is_single_org_user' | 'organisation_id'
>;

export function isAbodsUser(user: PublishHomeUser | null | undefined): boolean {
  return user?.account_type === ABODS_USER_ACCOUNT_TYPE;
}

export interface PublishHomeLinks {
  startView: string;
  reviewView: string;
}

/**
 * Where the publish home "Publish data" and "Review my data" links go for each
 * account type. Mirrors PublishHomeView.get_context_data
 * (transit_odp/publish/views/home.py).
 */
export function getPublishHomeLinks(user: PublishHomeUser | null | undefined): PublishHomeLinks {
  if (!user?.is_org_user) {
    const gatekeeper = publishAppPath('/gatekeeper');
    return { startView: gatekeeper, reviewView: gatekeeper };
  }

  if (isAbodsUser(user)) {
    const abodsGatekeeper = publishAppPath('/abods-gatekeeper');
    return { startView: abodsGatekeeper, reviewView: abodsGatekeeper };
  }

  if (user.is_agent_user) {
    return {
      startView: publishAppPath('/org'),
      reviewView: publishAppPath('/agent-dashboard'),
    };
  }

  if (user.organisation_id) {
    return {
      startView: publishAppPath(`/org/${user.organisation_id}/dataset`),
      reviewView: publishAppPath(`/org/${user.organisation_id}/dataset/timetable`),
    };
  }

  // Django always has an organisation for org users; fall back to the picker.
  return { startView: publishAppPath('/org'), reviewView: publishAppPath('/org') };
}
