'use client';

import { useState } from 'react';

type MatchingHelpVariant = 'overall' | 'feed';

interface AvlMatchingHelpModalProps {
  variant?: MatchingHelpVariant;
}

const MODAL_CONTENT: Record<MatchingHelpVariant, { heading: string; paragraphs: string[]; iconClass: string }> = {
  overall: {
    heading: 'Weekly overall AVL to Timetables data matching score',
    iconClass: 'help-icon-white',
    paragraphs: [
      'The weekly overall AVL to Timetables data matching score is an average weekly score of all your published data feeds on BODS.',
      'All the individual weekly report scores for all the published feeds you have on BODS are collected together and averaged to generate a weekly overall score. This weekly overall score is intended to give you an idea on how you are generally doing in terms of matching for all your published feeds on BODS. This is usually done on Monday every week. This is latest weekly matching score for all published feeds.',
      "Please note that BODS doesn't check every single packet of data but we do a random sampling throughout the day in order to determine these reports and scores.",
      "We also provide you with the last 4 weeks' matching reports to download. Please download the reports and work with your technology suppliers to provide the most accurate data so that data consumers and, eventually, your bus passengers can benefit.",
    ],
  },
  feed: {
    heading: 'AVL to Timetables feed sampled matching',
    iconClass: 'help-icon-blue',
    paragraphs: [
      'The AVL to Timetables feed matching is a weekly score of a published data feed. Daily random samples of data packets are collected for each published feed to be matched and then collated together to create a weekly report along with a weekly associated summary score for that report. This is usually done on Monday every week.',
      'This is the latest matching score for this feed.',
      "Please note that BODS doesn't check every single packet of data but we do a random sampling throughout the day in order to determine these reports and scores.",
      'Please download the report and work with your technology suppliers to provide the most accurate data so that download data consumers and eventually your bus passengers can benefit.',
    ],
  },
};

export function AvlMatchingHelpModal({ variant = 'overall' }: AvlMatchingHelpModalProps) {
  const [isOpen, setIsOpen] = useState(false);
  const content = MODAL_CONTENT[variant];

  return (
    <div className="help-modal">
      <i
        className={`${content.iconClass} fas fa-question-circle`}
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
            <h1 className="govuk-heading-m">{content.heading}</h1>
            {content.paragraphs.map((paragraph) => (
              <p key={paragraph} className="govuk-body">
                {paragraph}
              </p>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
