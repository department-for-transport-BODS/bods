import { publishAppPath } from '@/config/client';
import { getPublishHomeLinks, isAbodsUser } from './publish-home-links';

describe('getPublishHomeLinks', () => {
  it('sends non-organisation users to the gatekeeper for both links', () => {
    expect(getPublishHomeLinks({ account_type: 4, is_org_user: false })).toEqual({
      startView: publishAppPath('/gatekeeper'),
      reviewView: publishAppPath('/gatekeeper'),
    });
  });

  it('sends abods users to the abods gatekeeper for both links', () => {
    const user = { account_type: 6, is_org_user: true, organisation_id: 1 };

    expect(isAbodsUser(user)).toBe(true);
    expect(getPublishHomeLinks(user)).toEqual({
      startView: publishAppPath('/abods-gatekeeper'),
      reviewView: publishAppPath('/abods-gatekeeper'),
    });
  });

  it('sends agents to select-org and the agent dashboard', () => {
    expect(getPublishHomeLinks({ account_type: 5, is_org_user: true, is_agent_user: true, organisation_id: 1 })).toEqual({
      startView: publishAppPath('/org'),
      reviewView: publishAppPath('/agent-dashboard'),
    });
  });

  it('sends organisation users to their organisation', () => {
    expect(getPublishHomeLinks({ account_type: 2, is_org_user: true, organisation_id: 7 })).toEqual({
      startView: publishAppPath('/org/7/dataset'),
      reviewView: publishAppPath('/org/7/dataset/timetable'),
    });
  });

  it('treats a missing user as a non-organisation user', () => {
    expect(getPublishHomeLinks(null).startView).toBe(publishAppPath('/gatekeeper'));
    expect(isAbodsUser(null)).toBe(false);
  });
});
