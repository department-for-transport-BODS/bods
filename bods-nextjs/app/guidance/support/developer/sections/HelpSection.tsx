export function HelpSection({ supportEmail }: { supportEmail: string }) {
  return (
    <>
      <h1 className="govuk-heading-l">Data issues</h1>
      <p className="govuk-body">
        To report data issues, find the relevant data set/feed detail page and submit feedback to
        the data publisher.
      </p>
      <p className="govuk-body">
        Contact <a className="govuk-link" href={`mailto:${supportEmail}`}>{supportEmail}</a>{' '}
        for any queries not already answered in the developer documentation.
      </p>
    </>
  );
}

