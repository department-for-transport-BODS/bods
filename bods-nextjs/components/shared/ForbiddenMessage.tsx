/**
 * Django's 403 page (transit_odp/templates/403.html), shown when OrgUserViewMixin rejects a
 * signed-in user: ABODS users, non-org users and users from another organisation.
 */

'use client';

import { useEffect } from 'react';

export const FORBIDDEN_HEADING = 'We are sorry but you don’t have permissions to access this.';
export const FORBIDDEN_BODY = "Please liase with your organisation's admin for further information.";

export function ForbiddenMessage() {
  useEffect(() => {
    document.title = 'Forbidden (403)';
  }, []);

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-three-quarters">
            <h1 className="govuk-heading-xl">{FORBIDDEN_HEADING}</h1>
            <p className="govuk-body">{FORBIDDEN_BODY}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
