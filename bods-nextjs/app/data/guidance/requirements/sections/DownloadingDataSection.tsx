import Link from 'next/link';
import { dataPath } from '@/config/client';

export function DownloadingDataSection() {
  return (
    <>
      <h1 data-qa="downloading-header" className="govuk-heading-l">Downloading a data set</h1>
      <p className="govuk-body">
        A link to individual timetable and fares data sets can be found on their detail page when
        you{' '}
        <Link className="govuk-link" href={dataPath('/search')}>Browse for specific data</Link>. The
        link connects to the data hosted by the publishers. This link can be used to retrieve the
        latest version of the data.
      </p>
      <h1 data-qa="download-all-header" className="govuk-heading-l">Downloading all</h1>
      <p className="govuk-body">
        The Bus Open Data Service also caches data so that you can{' '}
        <Link className="govuk-link" href={dataPath('/downloads')}>Download all data</Link> directly
        from this service in a compressed Zip file. Historical real time data is not currently
        provided by the service.
      </p>
    </>
  );
}

