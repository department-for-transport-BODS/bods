import Link from 'next/link';
import { dataPath } from '@/config/client';
import { DataUpdatesTable } from '../DataUpdatesTable';
import { ApiResponseExample } from './ApiResponseExample';

const API_BASE = dataPath('/api/v1/');

export function UsingApiSection() {
  return (
    <>
      <h1 data-qa="using-api-header" className="govuk-heading-l">Using the APIs</h1>
      <p className="govuk-body">
        All data within the Bus Open Data Service can be queried and accessed via API calls. A
        different API call is required for each type of data (timetables, bus location).
      </p>
      <h1 data-qa="api-key-header" className="govuk-heading-l">API Key</h1>
      <p className="govuk-body">
        Use of the APIs requires an API key which can be obtained from{' '}
        <Link className="govuk-link" href="/account/settings">Account Settings.</Link>{' '}
        This key is linked to your account and should not be shared. If you have not already done
        so you will need to{' '}
        <Link className="govuk-link" href="/account/signup">register</Link> before you can access
        your API key.
      </p>
      <h1 className="govuk-heading-l">Data updates</h1>
      <p className="govuk-body">
        Data is updated and cached on the service. This is what is provided using the API. You
        will need to cache the data to generate historical data.
      </p>
      <DataUpdatesTable />
      <h2 className="govuk-heading-m">Timetables data</h2>
      <p className="govuk-body">
        To access the metadata associated with an individual data set, use the following API call:
      </p>
      <div className="dont-break-out govuk-body">
        {API_BASE}dataset/[DATASET_ID]/?api_key=[API_KEY]
      </div>
      <p className="govuk-body govuk-!-margin-top-4">
        where DATASET_ID is the id of the data set and API_KEY is your personal API key.
      </p>
      <p className="govuk-body">To search for data sets using the API, use the following API call:</p>
      <div className="dont-break-out govuk-body">
        {API_BASE}dataset/?[QUERY_PARAMS]&api_key=[API_KEY]
      </div>
      <p className="govuk-body govuk-!-margin-top-4">
        where QUERY_PARAMS are the query parameters as defined in the API reference and API_KEY
        is your personal API key.
      </p>
      <p className="govuk-body">Results are returned as JSON. For example,</p>
      <ApiResponseExample />
      <p className="govuk-body govuk-!-margin-top-4 govuk-!-padding-bottom-5">
        The url parameter provides a link to the published data.
      </p>
    </>
  );
}

