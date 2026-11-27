'use client';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCircleQuestion } from '@fortawesome/free-solid-svg-icons';
import { useState } from 'react';

/**
 * Help modal on the "Line" column header, from
 * publish/snippets/help_modals/line_service_number.html.
 */
export function LineHelpModal() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="help-modal">
      <FontAwesomeIcon
        icon={faCircleQuestion}
        className="help-icon"
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            setIsOpen(!isOpen);
          }
        }}
        role="button"
        tabIndex={0}
        aria-label="Help"
      />
      <div className={`overlay ${isOpen ? 'active' : ''}`}>
        <div className="window">
          <button type="button" className="close-button govuk-link" onClick={() => setIsOpen(false)}>
            Close
          </button>
          <div className="content">
            <h1 className="govuk-heading-m">Line</h1>
            <p className="govuk-body">
              Line, service number,&nbsp;route number or name by which the service is known and registered (eg. 17A,
              344 or Yeovile Route) The line numbers listed here are associated with the missing service code using
              the data from the OTC database.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
