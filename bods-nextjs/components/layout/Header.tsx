/**
 * Header Component
 * Matches Django header.html + navlinks_publish.html / navlinks_data.html.
 */

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useRef, useState, useEffect } from 'react';
import { HOSTS } from '@/config/client';
import type { BodsSubdomain } from '@/config/hosts';
import { useAuth } from '@/hooks/useAuth';
import { useBodsArea } from '@/lib/bods-host-context';
import type { User } from '@/types';
import { AccountIcon } from './icons/AccountIcon';
import { GovUkLogo } from './icons/GovUkLogo';

function pathFromHref(href: string): string {
  if (href.startsWith('http://') || href.startsWith('https://')) {
    return new URL(href).pathname;
  }

  return href;
}

function isServiceHost(area: BodsSubdomain): area is 'publish' | 'data' {
  return area === 'publish' || area === 'data';
}

function AccountMenuLinks({ area, user }: { area: 'publish' | 'data'; user: User }) {
  const accountUrl = '/account';
  const accountSettingsUrl = '/account/settings';
  const logoutUrl = '/account/logout';

  switch (area) {
    case 'publish': {
      const organisationProfileUrl = user.organisation_id
        ? `/account/manage/org-profile/${user.organisation_id}`
        : null;
      const userManagementUrl =
        user.is_org_admin && user.organisation_id
          ? `/account/manage/${user.organisation_id}`
          : null;

      return (
        <>
          <a className="govuk-link" href={accountUrl}>My account</a>
          {userManagementUrl && (
            <a className="govuk-link" href={userManagementUrl}>User management</a>
          )}
          {organisationProfileUrl && (
            <a className="govuk-link" href={organisationProfileUrl}>Organisation profile</a>
          )}
          <a className="govuk-link" href={accountSettingsUrl}>Account settings</a>
          <a className="govuk-link" href={logoutUrl}>Sign out</a>
        </>
      );
    }
    case 'data':
      return (
        <>
          <a className="govuk-link" href={accountUrl}>My account</a>
          <a className="govuk-link" href="/account/manage">Manage subscriptions</a>
          <a className="govuk-link" href={accountSettingsUrl}>Account settings</a>
          <a className="govuk-link" href={logoutUrl}>Sign out</a>
        </>
      );
    default: {
      const exhaustive: never = area;
      return exhaustive;
    }
  }
}

export function Header() {
  const { user } = useAuth();
  const pathname = usePathname();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLLIElement>(null);
  const area = useBodsArea();
  // Narrowed once so the account menu can be typed without re-checking the host.
  const serviceArea = isServiceHost(area) ? area : null;
  const homeUrl = HOSTS[area];
  // Each service host has its own guide-me page, as in Django's navlinks_publish /
  // navlinks_data snippets.
  const guideMeUrl = '/guide-me';
  const loginUrl = '/account/login';

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const serviceName = area === 'publish' ? 'Publish Bus Open Data' : 'Bus Open Data Service';
  const isActive = (href: string) => pathname === pathFromHref(href) ? 'govuk-header__navigation-item--active' : '';

  return (
    <header className="govuk-header" role="banner" data-module="govuk-header">
      <div className="govuk-header__container govuk-width-container">
        <div className="govuk-header__logo">
          <a href="https://www.gov.uk/" className="govuk-header__link govuk-header__link--homepage">
            <GovUkLogo />
          </a>
        </div>
        <div className="govuk-header__content">
          <Link href={homeUrl} className="govuk-header__link govuk-header__service-name">
            {serviceName}
          </Link>
          {serviceArea && (
            <nav className="govuk-header__navigation" aria-label="Menu">
              <button
                type="button"
                className="govuk-header__menu-button govuk-js-header-toggle"
                aria-controls="navigation"
                aria-label="Show or hide menu"
                hidden
              >
                Menu
              </button>
              <ul id="navigation" className="govuk-header__navigation-list flex-container govuk-!-width-full">
                <li className={`govuk-header__navigation-item ${isActive(homeUrl)}`}>
                  <Link className="govuk-header__link" href={homeUrl}>Home</Link>
                </li>
                <li className={`govuk-header__navigation-item ${isActive(guideMeUrl)}`}>
                  <Link className="govuk-header__link" href={guideMeUrl}>Guide me</Link>
                </li>
                <li className="flexfill" />
                {user ? (
                  <li
                    ref={dropdownRef}
                    className={`govuk-header__navigation-item dropdown bods-dropdown${dropdownOpen ? ' open' : ''}`}
                  >
                    <button
                      type="button"
                      className="govuk-header__link bods-dropdown__toggle"
                      onClick={() => setDropdownOpen((prev) => !prev)}
                      aria-expanded={dropdownOpen}
                      aria-haspopup="true"
                    >
                      <AccountIcon className="account-menu__icon" />
                      {' '}My account
                    </button>
                    <div className={`dropdown-content${dropdownOpen ? ' open' : ''}`}>
                      <AccountMenuLinks area={serviceArea} user={user} />
                    </div>
                  </li>
                ) : (
                  <li className="govuk-header__navigation-item">
                    <Link className="govuk-header__link" href={loginUrl}>Sign in</Link>
                  </li>
                )}
              </ul>
            </nav>
          )}
        </div>
      </div>
    </header>
  );
}
