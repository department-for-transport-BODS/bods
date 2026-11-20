'use client';

import Link from 'next/link';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { wwwPath } from '@/config/client';
import { useBodsArea } from '@/lib/bods-host-context';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';

export default function AccountInactivePage() {
  const area = useBodsArea();

  return (
    <div className="govuk-width-container">
      <Breadcrumbs
        items={hostBreadcrumbs(area, { label: 'Account Inactive', current: true })}
      />

      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Account Inactive</h1>
            <p className="govuk-body">
              Your account is inactive and you no longer have access to the Bus Open Data
              Service. If you were not expecting this then please{' '}
              <Link className="govuk-link" href={wwwPath('/contact')}>
                contact us
              </Link>
              .
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
