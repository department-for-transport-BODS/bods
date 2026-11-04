'use client';

type PublishCancelStepProps = {
  heading: string;
  confirmHref: string;
  onBack: () => void;
};

/**
 * Django's `feed_publish_cancel.html`: the cancel step a publish/update wizard renders at the same URL
 * after its Cancel submit button. Back and Cancel return to the previous step; Confirm leaves the wizard.
 */
export function PublishCancelStep({ heading, confirmHref, onBack }: Readonly<PublishCancelStepProps>) {
  return (
    <div className="govuk-width-container">
      <div className="govuk-breadcrumbs">
        <button type="button" className="govuk-back-link govuk-button-back-link" onClick={onBack}>
          Back
        </button>
      </div>
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">{heading}</h1>
            <p className="govuk-body">Any changes you have made so far will not be saved.</p>
            <div className="btn-group-justified">
              <a role="button" className="govuk-button app-!-mr-sm-4" href={confirmHref}>
                Confirm
              </a>
              <button type="button" className="govuk-button govuk-button--secondary" onClick={onBack}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
