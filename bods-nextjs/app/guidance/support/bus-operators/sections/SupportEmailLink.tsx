/**
 * Support Email Link Component
 * Renders a linked email address using the configured SUPPORT_EMAIL.
 */

import { SUPPORT_EMAIL } from '@/lib/config';

export function SupportEmailLink() {
  return (
    <a className="govuk-link" href={`mailto:${SUPPORT_EMAIL}`}>
      {SUPPORT_EMAIL}
    </a>
  );
}


