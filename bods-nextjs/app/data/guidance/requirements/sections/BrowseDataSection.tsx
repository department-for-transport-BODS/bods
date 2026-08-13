export function BrowseDataSection() {
  return (
    <>
      <h1 className="govuk-heading-l">Browse for specific data</h1>
      <p className="govuk-body">
        Publishers supply data sets and feeds to BODS. You can view, download and provide
        feedback on these individually when you browse and open each detail page.
      </p>
      <h2 className="govuk-heading-m">Data detail page</h2>
      <p className="govuk-body">Each data set/feed detail page includes:</p>
      <ul className="govuk-list govuk-list--bullet">
        <li>Metadata</li>
        <li>Changelog</li>
        <li>API calls with that data set ID</li>
        <li>Feedback</li>
        <li>Subscription options</li>
        <li>Underlying source links for static data types</li>
      </ul>
    </>
  );
}

