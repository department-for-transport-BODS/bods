/**
 * Header Component
 * Matches Django header.html + navlinks_publish.html exactly.
 */

'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useRef, useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { AccountIcon } from './icons/AccountIcon';
import { GovUkLogo } from './icons/GovUkLogo';

export function Header() {
  const { user } = useAuth();
  const pathname = usePathname();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLLIElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const isPublish = pathname?.startsWith('/publish');
  const isData = pathname?.startsWith('/data');
  const showServiceMenu = Boolean(isPublish || isData);
  const serviceName = isPublish ? 'Publish Bus Open Data' : 'Bus Open Data Service';
  let serviceHomeUrl = '/';
  if (isPublish) {
    serviceHomeUrl = '/publish';
  } else if (isData) {
    serviceHomeUrl = '/data';
  }

  const isActive = (href: string) => pathname === href ? 'govuk-header__navigation-item--active' : '';

  return (
    <header className="govuk-header" role="banner" data-module="govuk-header">
      <div className="govuk-header__container govuk-width-container">
        <div className="govuk-header__logo">
          <a href="https://www.gov.uk/" className="govuk-header__link govuk-header__link--homepage">
            <GovUkLogo />
          </a>
        </div>
        <div className="govuk-header__content">
          <Link href={serviceHomeUrl} className="govuk-header__link govuk-header__service-name">
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
                <li className={`govuk-header__navigation-item ${isActive(serviceHomeUrl)}`}>
                  <Link className="govuk-header__link" href={serviceHomeUrl}>Home</Link>
                </li>
                <li className={`govuk-header__navigation-item ${isActive('/publish/guide-me')}`}>
                  <Link className="govuk-header__link" href="/publish/guide-me">Guide me</Link>
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
                      <a className="govuk-link" href="/publish/account">My account</a>
                      <a className="govuk-link" href="/publish/account">Organisation profile</a>
                      <a className="govuk-link" href="/publish/account">Account settings</a>
                      <a className="govuk-link" href="/account/logout">Sign out</a>
                    </div>
                  </li>
                ) : (
                  <li className="govuk-header__navigation-item">
                    <Link className="govuk-header__link" href="/account/login">Sign in</Link>
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
