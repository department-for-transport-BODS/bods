/**
 * 404 Not Found Page
 *
 * Source: transit_odp/templates/404.html (extends error_base.html)
 *
 * Shown for every unknown path on every host, and for resources that don't exist
 * (e.g. a dataset id that isn't found). Django's version has no breadcrumbs.
 */

import Link from 'next/link';
import { wwwPath } from '@/config/client';

export const metadata = {
  title: 'Page not found - Bus Open Data Service',
};

export default function NotFound() {
  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper app-main-class">
        <div className="govuk-grid-row govuk-!-margin-top-9 govuk-!-margin-bottom-9">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-l">Page not found</h1>

            <p className="govuk-body">
              If you typed the web address, check it is correct.
            </p>

            <p className="govuk-body">
              If you pasted the web address, check you copied the entire address.
            </p>

            <p className="govuk-body">
              If the web address is correct or you selected a link or button,{' '}
              <Link href={wwwPath('/contact')} className="govuk-link">
                contact Bus open data support line
              </Link>{' '}
              if you need to speak to someone about this service.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

