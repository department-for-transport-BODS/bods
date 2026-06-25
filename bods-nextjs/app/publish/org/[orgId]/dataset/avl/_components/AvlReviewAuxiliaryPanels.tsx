import Link from 'next/link';

type AvlReviewHelpAsideProps = {
  supportBusOperatorsUrl: string;
  contactSupportUrl: string;
};

export function AvlReviewHelpAside({ supportBusOperatorsUrl, contactSupportUrl }: AvlReviewHelpAsideProps) {
  return (
    <div className="govuk-grid-column-one-third">
      <h2 className="govuk-heading-m">Need help with operator data requirements?</h2>
      <ul className="govuk-list app-list--nav govuk-!-font-size-19">
        <li>
          <a className="govuk-link" href={supportBusOperatorsUrl}>View our guidelines here</a>
        </li>
        <li>
          <a className="govuk-link" href={contactSupportUrl}>Contact support desk</a>
        </li>
      </ul>
    </div>
  );
}

type AvlReviewErrorGuidanceProps = {
  deleteUrl: string;
};

export function AvlReviewErrorGuidance({ deleteUrl }: AvlReviewErrorGuidanceProps) {
  return (
    <>
      <h3 className="govuk-heading-m">What should I do next?</h3>
      <p className="govuk-body govuk-!-font-size-19">
        You can refer to the documentation or contact support to help you fix this.
      </p>
      <p className="govuk-!-font-size-19 checkbox-filter__annotation govuk-body">
        Accepted formats include SIRI-VM
      </p>
      <div className="btn-group-justified">
        <Link role="button" className="govuk-button govuk-button--secondary" href={deleteUrl}>
          Delete data feed
        </Link>
      </div>
    </>
  );
}
