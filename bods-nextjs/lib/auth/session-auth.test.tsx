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

  it('preserves the session cookie age', () => {
    expect(
      normaliseUser({ id: 1, email: 'a@example.com', session_cookie_age: 600 }).session_cookie_age,
    ).toBe(600);
  });
});
