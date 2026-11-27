'use client';

import { useState, type ReactNode } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCircleQuestion } from '@fortawesome/free-solid-svg-icons';

interface DownloadHelpModalProps {
  heading: string;
  children: ReactNode;
}

/**
 * Source: transit_odp/templates/snippets/help_modal_base.html
 * Behaviour: transit_odp/frontend/assets/js/help-modal.js (open on icon click,
 * close via the Close button or by clicking the overlay).
 */
export function DownloadHelpModal({ heading, children }: DownloadHelpModalProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="help-modal">
      <FontAwesomeIcon
        icon={faCircleQuestion}
        className="help-icon"
        onClick={() => setIsOpen(true)}
        onKeyDown={(event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            setIsOpen(true);
          }
        }}
        role="button"
        tabIndex={0}
        aria-label={`Help: ${heading}`}
      />
      <div
        className={`overlay ${isOpen ? 'active' : ''}`}
        data-testid="help-overlay"
        onClick={(event) => {
          if (event.target === event.currentTarget) {
            setIsOpen(false);
          }
        }}
      >
        <div className="window">
          <button type="button" className="close-button govuk-link" onClick={() => setIsOpen(false)}>
            Close
          </button>
          <div className="content">
            <h1 className="govuk-heading-m">{heading}</h1>
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
