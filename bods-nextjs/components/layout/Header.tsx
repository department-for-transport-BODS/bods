/**
 * Header Component
 * Matches Django header.html + navlinks_publish.html exactly.
 */

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useRef, useState, useEffect } from 'react';
import { HOSTS, publishPath } from '@/config/client';
import { bodsAreaFromHostname, type BodsSubdomain } from '@/config/hosts';
import { useAuth } from '@/hooks/useAuth';
import { AccountIcon } from './icons/AccountIcon';
import { GovUkLogo } from './icons/GovUkLogo';

function serviceHomeUrl(area: BodsSubdomain): string {
  switch (area) {
    case 'publish':
      return HOSTS.publish;
    case 'data':
      return HOSTS.data;
    case 'admin':
      return HOSTS.admin;
    case 'www':
      return HOSTS.www;
    default: {
      const exhaustive: never = area;
      return exhaustive;
    }
  }
}

function pathFromHref(href: string): string {
  if (href.startsWith('http://') || href.startsWith('https://')) {
    return new URL(href).pathname;
  }

  return href;
}

export function Header({ hostname }: { hostname: string }) {
  const { user } = useAuth();
  const pathname = usePathname();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLLIElement>(null);
  const area = bodsAreaFromHostname(hostname);
  const showServiceMenu = area === 'publish' || area === 'data';
  const homeUrl = serviceHomeUrl(area);
  const guideMeUrl = publishPath('/guide-me');
  const accountUrl = publishPath('/account');
  const loginUrl = '/account/login';
  const logoutUrl = '/account/logout';

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
          {showServiceMenu && (
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
                      <a className="govuk-link" href={accountUrl}>My account</a>
                      <a className="govuk-link" href={accountUrl}>Organisation profile</a>
                      <a className="govuk-link" href={accountUrl}>Account settings</a>
                      <a className="govuk-link" href={logoutUrl}>Sign out</a>
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
