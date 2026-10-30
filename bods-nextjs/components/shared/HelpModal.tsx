'use client';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCircleQuestion } from '@fortawesome/free-solid-svg-icons';
import { useState, type ReactNode } from 'react';

interface HelpModalProps {
  heading: string;
  children: ReactNode;
  /** Replaces the default blue question-mark trigger (e.g. the licence compliance dot). */
  icon?: ReactNode;
}

/**
 * Next.js equivalent of Django's `snippets/help_modal_base.html`: an icon that
 * toggles a full-screen overlay window with a Close button and a heading.
 * Styles live under `.help-modal` in globals.css.
 */
export function HelpModal({ heading, children, icon }: HelpModalProps) {
  const [isOpen, setIsOpen] = useState(false);
  const toggle = () => setIsOpen((open) => !open);

  return (
    <div className="help-modal">
      {icon ? (
        <span
          role="button"
          tabIndex={0}
          aria-label="Help"
          onClick={toggle}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              toggle();
            }
          }}
        >
          {icon}
        </span>
      ) : (
        <FontAwesomeIcon
          icon={faCircleQuestion}
          className="help-icon-blue"
          onClick={toggle}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              toggle();
            }
          }}
          role="button"
          tabIndex={0}
          aria-label="Help"
        />
      )}
      <div className={`overlay${isOpen ? ' active' : ''}`}>
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
