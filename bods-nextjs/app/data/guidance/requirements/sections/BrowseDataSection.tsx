import Link from 'next/link';
import { dataPath } from '@/config/client';

export function BrowseDataSection() {
  return (
    <>
      <h1 data-qa="browse-header" className="govuk-heading-l">Browse for specific data</h1>
      <p className="govuk-body">
        Publishers supply data sets and data feeds to the Bus Open Data Service. You can view,
        download or feedback on these individually when you{' '}
        <Link className="govuk-link" href={dataPath('/search')}>Browse for specific data</Link>{' '}
        and click on the data to find its detail page.
      </p>
      <h2 data-qa="data-detail-header" className="govuk-heading-l">Data detail page</h2>
      <p className="govuk-body">
        Each data set/feed supplied to the service has a detail page, where you can view:
      </p>
      <ul className="govuk-list govuk-list--bullet">
        <li>Metadata</li>
        <li>Changelog</li>
        <li>API call with that data set ID</li>
        <li>Feedback box</li>
        <li>Subscription options</li>
        <li>Link to underlying data for static data types</li>
      </ul>
      <h2 data-qa="feedback-header" className="govuk-heading-l">Feedback</h2>
      <p className="govuk-body">
        Feedback will be sent via email to the data publisher, enhancing the feedback loop
        between developers and publishers, in turn improving the overall data quality.
      </p>
      <h2 data-qa="subscribe-header" className="govuk-heading-l">Subscribe</h2>
      <p className="govuk-body">
        In the detail page you can subscribe to data sets/feeds so you will receive email
        notifications if the publisher makes any changes.
      </p>
      <h2 data-qa="search-header" className="govuk-heading-l">Search bar functionality</h2>
      <p className="govuk-body">
        The search bar matches terms entered against metadata such as the title, description or
        data ID.
      </p>
    </>
  );
}

