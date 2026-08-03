import Link from 'next/link';

export function QuickStartSection() {
  return (
    <>
      <h1 className="govuk-heading-l">Quick start</h1>
      <h2 className="govuk-heading-m">APIs</h2>
      <p className="govuk-body">
        Start calling data using{' '}
        <Link className="govuk-link" href="?section=api">
          Using the APIs
        </Link>
        . A different API is required to consume each data type.
      </p>
      <p className="govuk-body">
        Query parameters are documented in the{' '}
        <Link className="govuk-link" href="?section=apireference">
          API reference
        </Link>
        .
      </p>
      <p className="govuk-body">
        You must <Link className="govuk-link" href="/account/signup">register</Link> for an account to get an API key.
      </p>

      <h2 className="govuk-heading-m">Download all data</h2>
      <p className="govuk-body">
        <Link className="govuk-link" href="/data">
          Download all data
        </Link>{' '}
        will give you all data cached by the service for your chosen data type.
      </p>

      <h2 className="govuk-heading-m">Data provided to service</h2>
      <p className="govuk-body">
        <Link className="govuk-link" href="/data">
          Browse for specific data
        </Link>{' '}
        to look for examples of data published to the service, find a data set detail page,
        view metadata, identify data set IDs and download data.
      </p>

      <h2 className="govuk-heading-m">Status</h2>
      <table className="govuk-table">
        <thead className="govuk-table__head">
          <tr className="govuk-table__row">
            <th scope="col" className="govuk-table__header">Data set status</th>
            <th scope="col" className="govuk-table__header">Explanation</th>
          </tr>
        </thead>
        <tbody className="govuk-table__body">
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Published</td>
            <td className="govuk-table__cell">Data that has been published.</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Inactive</td>
            <td className="govuk-table__cell">Data intentionally removed from a published state.</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Error</td>
            <td className="govuk-table__cell">URL-based publishing failed validation during an update pull.</td>
          </tr>
        </tbody>
      </table>
    </>
  );
}

