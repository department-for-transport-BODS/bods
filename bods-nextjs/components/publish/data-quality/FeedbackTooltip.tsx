'use client';

import type { KeyboardEvent } from 'react';

type FeedbackTooltipProps = {
  id: string;
  label: string;
  feedback: string;
  isOpen: boolean;
  onToggle: () => void;
};

// Source: transit_odp/dqs/templates/dqs/snippets/dqs_warning_detail.html (is_show_popup column)
export function FeedbackTooltip({ id, label, feedback, isOpen, onToggle }: FeedbackTooltipProps) {
  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget && (event.key === 'Enter' || event.key === ' ')) {
      event.preventDefault();
      onToggle();
    }
  };

  return (
    <div
      className="tooltip govuk-link"
      title="More information"
      role="button"
      tabIndex={0}
      aria-expanded={isOpen}
      aria-controls={id}
      onClick={onToggle}
      onKeyDown={onKeyDown}
    >
      {label}
      <p
        className={`tooltiptext${isOpen ? ' showtooltip' : ''}`}
        style={{ width: 350 }}
        id={id}
        role="dialog"
        onClick={(event) => event.stopPropagation()}
      >
        <span>{feedback}</span>
        <br />
        <button
          type="button"
          className="govuk-button govuk-button--secondary govuk-!-margin-top-2 govuk-!-margin-bottom-1"
          data-module="govuk-button"
          onClick={onToggle}
        >
          Close
        </button>
      </p>
    </div>
  );
}
