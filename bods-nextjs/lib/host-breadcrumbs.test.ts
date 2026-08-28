import { HOSTS } from '@/config/client';
import { hostBreadcrumbs, serviceHomeName } from './host-breadcrumbs';

describe('hostBreadcrumbs', () => {
  it('adds the publish home crumb on publish', () => {
    expect(hostBreadcrumbs('publish', { label: 'Sign in', current: true })).toEqual([
      { label: 'Bus Open Data Service', href: HOSTS.www },
      { label: 'Publish Bus Open Data', href: HOSTS.publish },
      { label: 'Sign in', current: true },
    ]);
  });

  it('adds the find home crumb on data', () => {
    expect(hostBreadcrumbs('data', { label: 'Sign in', current: true })).toEqual([
      { label: 'Bus Open Data Service', href: HOSTS.www },
      { label: 'Find Bus Open Data', href: HOSTS.data },
      { label: 'Sign in', current: true },
    ]);
  });

  it('skips a duplicate home crumb on www', () => {
    expect(hostBreadcrumbs('www', { label: 'Sign in', current: true })).toEqual([
      { label: 'Bus Open Data Service', href: HOSTS.www },
      { label: 'Sign in', current: true },
    ]);
  });

  it('names the admin home', () => {
    expect(serviceHomeName('admin')).toBe('BODS admin home');
    expect(hostBreadcrumbs('admin')[1]).toEqual({
      label: 'BODS admin home',
      href: HOSTS.admin,
    });
  });
});
