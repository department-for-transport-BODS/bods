/** @jest-environment node */

import { HOSTS } from '@/config/client';
import { loginUrlWithNext, resolvePostLoginRedirect } from './post-login-redirect';

describe('post-login-redirect', () => {
  it('falls back to www home when next is missing', () => {
    expect(resolvePostLoginRedirect(null)).toBe(HOSTS.www);
  });

  it('allows relative paths on www', () => {
    expect(resolvePostLoginRedirect('/account')).toBe('/account');
  });

  it('allows absolute URLs on known BODS hosts', () => {
    const next = `${HOSTS.data}/api`;
    expect(resolvePostLoginRedirect(next)).toBe(next);
  });

  it('rejects external hosts', () => {
    expect(resolvePostLoginRedirect('https://evil.example/phish')).toBe(HOSTS.www);
  });

  it.each(['//evil.example', '/\\evil.example', '/\\/evil.example'])(
    'rejects %s, which browsers resolve to another origin',
    (next) => {
      expect(resolvePostLoginRedirect(next)).toBe(HOSTS.www);
    },
  );

  it('adds next to the login URL', () => {
    const url = loginUrlWithNext(wwwish(), `${HOSTS.data}/api`);
    expect(url).toContain('next=');
    expect(decodeURIComponent(new URL(url).searchParams.get('next')!)).toBe(`${HOSTS.data}/api`);
  });

  it('keeps a relative login URL on the host the user came from', () => {
    const url = loginUrlWithNext('/account/login', `${HOSTS.data}/api`);
    expect(url.startsWith(`${HOSTS.data}/account/login`)).toBe(true);
    expect(decodeURIComponent(new URL(url).searchParams.get('next')!)).toBe(`${HOSTS.data}/api`);
  });
});

function wwwish() {
  return `${HOSTS.www}/account/login`;
}
