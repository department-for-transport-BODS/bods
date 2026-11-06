import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Thank you',
};

export default function FeedbackThankYouPage() {
  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-l app-!-mb-4">Thank you for getting in touch</h1>
            <p className="govuk-body">Your feedback helps to improve our service.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
