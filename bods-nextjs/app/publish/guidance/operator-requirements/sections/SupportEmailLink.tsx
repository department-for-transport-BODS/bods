/**
 * Support Email Link Component
 * Renders a linked email address using the configured support email.
 */

import { useSupportConfig } from '@/components/shared/SupportConfigProvider';

export function SupportEmailLink() {
  const { supportEmail } = useSupportConfig();

  return (
    <a className="govuk-link" href={`mailto:${supportEmail}`}>
      {supportEmail}
    </a>
  );
}


