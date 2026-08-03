/**
 * Support Email Link Component
 * Renders a linked email address using the configured support email.
 */

import { config } from '@/config';

export function SupportEmailLink() {
  return (
    <a className="govuk-link" href={`mailto:${config.supportEmail}`}>
      {config.supportEmail}
    </a>
  );
}


