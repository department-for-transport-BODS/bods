import { DESTINATIONS } from './GuideMeRedirect';
import type { User } from '@/types';

const makeUser = (overrides: Partial<User>): User => ({ ...overrides }) as User;

describe('GuideMeRedirect DESTINATIONS.activity', () => {
  it('sends agents to the agent dashboard with next/prev params like Django', () => {
    expect(DESTINATIONS.activity(makeUser({ is_agent_user: true, organisation_id: 7 }))).toBe(
      '/agent-dashboard?next=data-activity&prev=guide-me',
    );
  });

  it('sends org users to their data activity page with prev=guide-me', () => {
    expect(DESTINATIONS.activity(makeUser({ is_agent_user: false, organisation_id: 7 }))).toBe(
      '/org/7/dataset/data-activity?prev=guide-me',
    );
  });

  it('falls back to the organisation selector without an organisation', () => {
    expect(DESTINATIONS.activity(makeUser({ is_agent_user: false }))).toBe('/org');
  });
});
