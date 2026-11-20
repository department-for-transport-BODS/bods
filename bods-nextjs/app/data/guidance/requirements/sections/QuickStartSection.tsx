import Link from 'next/link';
import { dataPath } from '@/config/client';
import { DataUpdatesTable } from '../DataUpdatesTable';

export function QuickStartSection() {
  return (
    <>
      <h1 data-qa="quick-start-header" className="govuk-heading-l">Quick start</h1>
      <h2 data-qa="apis-header" className="govuk-heading-m">APIs</h2>
      <p className="govuk-body">
        Start calling data <Link className="govuk-link" href="?section=api">Using the APIs</Link>.
        A different API is required to consume each data type.
      </p>
      <p className="govuk-body">
        Query parameters are documented in the{' '}
        <Link className="govuk-link" href="?section=apireference">API reference</Link>.
      </p>
      <p className="govuk-body">
        You must <Link className="govuk-link" href="/account/signup">register</Link> for
        an account to get an API key.
      </p>

      <h2 data-qa="download-all-header" className="govuk-heading-m">Download all data</h2>
      <p className="govuk-body">
        <Link className="govuk-link" href={dataPath('/downloads')}>Download all data</Link> will give
        you all data cached by the service for your chosen data type. All data set statuses are
        included in the download all, including: Published and Inactive.
      </p>

      <h2 data-qa="data-service-header" className="govuk-heading-m">Data provided to service</h2>
      <p className="govuk-body">
        <Link className="govuk-link" href={dataPath('/search')}>Browse for specific data</Link> to:
      </p>
      <ul className="govuk-list govuk-list--bullet">
        <li>Look for examples of data published to the service</li>
        <li>Find a data set&rsquo;s detail page</li>
        <li>View a data set&rsquo;s metadata</li>
        <li>Find a data set&rsquo;s ID</li>
        <li>Download a data set</li>
        <li><strong>Provide feedback to data publishers about a certain data set</strong></li>
      </ul>

      <h2 data-qa="data-updates-header" className="govuk-heading-m">Data updates</h2>
      <DataUpdatesTable />

      <h2 data-qa="status-header" className="govuk-heading-m">Status</h2>
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
            <td className="govuk-table__cell">Data that has been published</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Inactive</td>
            <td className="govuk-table__cell">
              If a publisher actively wants to remove data from a published state, they can
              move it to an inactive state
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Error</td>
            <td className="govuk-table__cell">
              If the publisher users a URL link to publish and the URL link fails to validate
              during the daily pull from BODS, then the data set will move into error but
              however the old data will still be available
            </td>
          </tr>
        </tbody>
      </table>

      <table className="govuk-table">
        <thead className="govuk-table__head">
          <tr className="govuk-table__row">
            <th scope="col" className="govuk-table__header">Data feed status</th>
            <th scope="col" className="govuk-table__header">Explanation</th>
          </tr>
        </thead>
        <tbody className="govuk-table__body">
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Published</td>
            <td className="govuk-table__cell">Data that has been published</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">No vehicle activity</td>
            <td className="govuk-table__cell">
              Data feeds provide location data and can either be in a published or error state.
              Error states are given to feeds when:
              <ol className="govuk-list govuk-list--number">
                <li>Feeds are unable to make a connection</li>
                <li>No data has been provided for over 5 minutes during the day</li>
              </ol>
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Inactive</td>
            <td className="govuk-table__cell">
              If a publisher actively wants to remove data from a published state, they can
              move it to an inactive state.
            </td>
          </tr>
        </tbody>
      </table>

      <h2 data-qa="what-is-header" className="govuk-heading-m">What is a data set/feed?</h2>
      <p className="govuk-body">
        Operators must provide a complete set of data regarding local bus services. They may
        provide this as a single data set or break it down into multiple data sets, depending on
        their own business needs. Commonly operators break the data down into data sets per:
      </p>
      <ul className="govuk-list govuk-list--bullet">
        <li>Operating companies</li>
        <li>Regions of operation</li>
        <li>Underlying scheduler</li>
        <li>Route or line</li>
        <li>Data source / system supplying data</li>
      </ul>
    </>
  );
}

