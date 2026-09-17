import Link from 'next/link';
import { dataPath } from '@/config/client';

export function DataByOperatorSection() {
  return (
    <>
      <h2 data-qa="operator-header" className="govuk-heading-l">Getting data by operator</h2>
      <p className="govuk-body">
        For all data types you can apply the NOC query parameter. This will limit results to data
        published by that operator, including any other NOC associated with that operator on
        this service.
      </p>
      <p className="govuk-body">
        Download the{' '}
        <Link className="govuk-link" href={dataPath('/catalogue')}>data catalogue</Link> to see
        the relationship between operators and NOC on this service.
      </p>
      <h2 data-qa="operator-header" className="govuk-heading-l">Getting data by location</h2>
      <p className="govuk-body">
        To get data for a specific location you can use the boundingBox parameter. For bus
        location data this will limit the data to vehicles within the prescribed area at that
        point in time. For timetables are fares if any data is within the boundingBox, the whole
        data set will be returned.
      </p>
      <p className="govuk-body">
        For more information on API query parameters please go to the{' '}
        <Link className="govuk-link" href="?section=apireference">API reference</Link>.
      </p>
    </>
  );
}

