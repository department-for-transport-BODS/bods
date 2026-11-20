import { normaliseUser } from './session-auth';

describe('normaliseUser', () => {
  it('preserves routing fields', () => {
    expect(
      normaliseUser({
        id: 12,
        email: 'publisher@example.com',
        account_type: 2,
        organisation_id: 34,
        is_org_user: true,
        is_single_org_user: true,
        is_agent_user: false,
      }),
    ).toMatchObject({
      id: 12,
      email: 'publisher@example.com',
      account_type: 2,
      organisation_id: 34,
      is_org_user: true,
      is_single_org_user: true,
      is_agent_user: false,
    });
  });
});
