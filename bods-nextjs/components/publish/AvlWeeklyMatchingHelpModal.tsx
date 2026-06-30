'use client';

import { useState } from 'react';

export function AvlWeeklyMatchingHelpModal() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="help-modal">
      <i
        className="help-icon-white fas fa-question-circle"
        onClick={() => setIsOpen(!isOpen)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            setIsOpen(!isOpen);
          }
        }}
        role="button"
        tabIndex={0}
        aria-label="Help"
      />
      <div className={`overlay ${isOpen ? 'active' : ''}`}>
        <div className="window">
          <button
            type="button"
            className="close-button govuk-link"
            onClick={() => setIsOpen(false)}
          >
            Close
          </button>
          <div className="content">
            <h1 className="govuk-heading-m">
              Weekly overall AVL to Timetables data matching score
            </h1>
            <p className="govuk-body">
              The weekly overall AVL to Timetables data matching score is an average weekly score of
              all your published data feeds on BODS.
            </p>
            <p className="govuk-body">
              All the individual weekly report scores for all the published feeds you have on BODS
              are collected together and averaged to generate a weekly overall score. This weekly
              overall score is intended to give you an idea on how you are generally doing in terms
              of matching for all your published feeds on BODS. This is usually done on Monday every
              week. This is latest weekly matching score for all published feeds.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
