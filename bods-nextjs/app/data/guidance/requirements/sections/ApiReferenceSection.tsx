import Link from 'next/link';
import { dataPath } from '@/config/client';

const API_BASE = dataPath('/api/v1/');

export function ApiReferenceSection() {
  return (
    <>
      <h1 data-qa="api-ref-header" className="govuk-heading-l">API reference</h1>
      <p className="govuk-body">
        The API reference contains details of API calls, query parameters and error codes. You
        can try out API calls in an interactive sandbox,{' '}
        <Link className="govuk-link-bold" href={dataPath('/api')}>Access interactive API.</Link>
      </p>

      <h2 data-qa="all-data-header" className="govuk-heading-m">All data API reference</h2>
      <p className="govuk-body">
        You can use the call all data APIs in your code. This will provide all data currently
        available.
      </p>
      <table className="govuk-table govuk-!-margin-bottom-9">
        <thead className="govuk-table__head">
          <tr className="govuk-table__row">
            <th scope="col" className="w-40-l govuk-table__header">Data</th>
            <th scope="col" className="govuk-table__header">Call all data APIs</th>
          </tr>
        </thead>
        <tbody className="govuk-table__body">
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Timetables</td>
            <td className="govuk-table__cell">{API_BASE}dataset/?api_key=[API_KEY]</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Bus location</td>
            <td className="govuk-table__cell">{API_BASE}datafeed/?api_key=[API_KEY]</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Fares</td>
            <td className="govuk-table__cell">{API_BASE}fares/dataset/?api_key=[API_KEY]</td>
          </tr>
        </tbody>
      </table>

      <h2 data-qa="timetable-header" className="govuk-heading-m">Timetables data API parameters</h2>
      <p className="govuk-body">
        Data sets provided may contain multiple TransXChange files. Therefore, query parameters
        will return any data sets which contains at least one TransXChange file that satisfies
        your query parameters.
      </p>
      <table className="govuk-table govuk-!-margin-bottom-9">
        <thead className="govuk-table__head">
          <tr className="govuk-table__row">
            <th scope="col" className="w-30-l govuk-table__header">Name</th>
            <th scope="col" className="govuk-table__header">Description</th>
          </tr>
        </thead>
        <tbody className="govuk-table__body">
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">adminArea</td>
            <td className="govuk-table__cell">
              adminArea is a field within the data, and therefore if any of the TransXChange
              files within a specific data set has the specified adminArea the whole data set
              will be returned. A list of adminAreas can be found on the NPTG website:{' '}
              <a
                className="govuk-link"
                href="https://data.gov.uk/dataset/3b1766bf-04a3-44f5-bea9-5c74cf002e1d/national-public-transport-gazetteer-nptg"
                target="_blank"
                rel="noopener noreferrer"
              >
                https://data.gov.uk/dataset/3b1766bf-04a3-44f5-bea9-5c74cf002e1d/national-public-transport-gazetteer-nptg
              </a>
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">endDateStart</td>
            <td className="govuk-table__cell">
              Limit results to data sets with services with end dates after this date. String
              formatted as YYYY-MM-DDTHH:MM:SS.
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">endDateEnd</td>
            <td className="govuk-table__cell">
              Limit results to data sets with services with end dates before this date. String
              formatted as YYYY-MM-DDTHH:MM:SS.
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">limit</td>
            <td className="govuk-table__cell">The maximum number of records to return.</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">modifiedDate</td>
            <td className="govuk-table__cell">
              Limit results to data sets that have been created/updated since the specified date.
              String formatted as YYYY-MM-DDTHH:MM:SS.
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">noc</td>
            <td className="govuk-table__cell">
              Input a comma separated list of National Operator Codes to limit results to data
              sets of the publishers associated to the specified National Operator Code. A
              publisher may have multiple National Operator Codes associated with it. Your
              response will include data for all National Operator Codes associated with that
              publisher. Not just those included in the query parameter. National Operator codes
              can be found on the Traveline website,{' '}
              <a
                className="govuk-link"
                href="https://www.travelinedata.org.uk/traveline-open-data/transport-operations/about-2/"
                target="_blank"
                rel="noopener noreferrer"
              >
                https://www.travelinedata.org.uk/traveline-open-data/transport-operations/about-2/
              </a>
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">offset</td>
            <td className="govuk-table__cell">
              Return results that match the query starting from the specified offset. e.g.
              &amp;offset=10&amp;limit=25 returns results from 11 to 35. The default is set to 0.
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">search</td>
            <td className="govuk-table__cell">
              Return data sets where the data set name, data set description, organisation name,
              or admin area name contain the specified value.
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">status</td>
            <td className="govuk-table__cell">
              Limit results to data sets with the specified status String, accepted values are
              published, inactive.
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">startDateStart</td>
            <td className="govuk-table__cell">
              Limit results to data sets with services with start dates after this date. String
              formatted as YYYY-MM-DDTHH:MM:SS.
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">startDateEnd</td>
            <td className="govuk-table__cell">
              Limit results to data sets with services with start dates before this date. String
              formatted as YYYY-MM-DDTHH:MM:SS.
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">datasetID</td>
            <td className="govuk-table__cell">
              Limit results to a specific data set of a publisher using the data set ID.
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">dqRag</td>
            <td className="govuk-table__cell">
              Limit results to data sets with the specified String value, accepted values are
              red, amber, green.
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">bodsCompliance</td>
            <td className="govuk-table__cell">
              Limit results to data sets with the specified boolean value.
            </td>
          </tr>
        </tbody>
      </table>

      <h2 data-qa="fares-header" className="govuk-heading-m">Fares data API parameters</h2>
      <p className="govuk-body">
        Data sets provided may contain multiple NeTEx files. Therefore, query parameters will
        return all data sets which contain at least one NeTEx file that satisfied your query
        parameters.
      </p>
      <table className="govuk-table govuk-!-margin-bottom-9">
        <thead className="govuk-table__head">
          <tr className="govuk-table__row">
            <th scope="col" className="w-30-l govuk-table__header">Name</th>
            <th scope="col" className="govuk-table__header">Description</th>
          </tr>
        </thead>
        <tbody className="govuk-table__body">
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">noc</td>
            <td className="govuk-table__cell">
              Input a comma separated list of National Operator Codes to limit results to data
              sets of the publishers associated to the specified National Operator Code. A
              publisher may have multiple National Operator Codes associated with it. Your
              response will include data for all National Operator Codes associated with that
              publisher. Not just those included in the query parameter. National Operator codes
              can be found on the Traveline website,{' '}
              <a
                className="govuk-link"
                target="_blank"
                rel="noopener noreferrer"
                href="https://www.travelinedata.org.uk/traveline-open-data/transport-operations/about-2/"
              >
                https://www.travelinedata.org.uk/traveline-open-data/transport-operations/about-2/
              </a>.
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">status</td>
            <td className="govuk-table__cell">
              Limit results to data sets with the specified status. Accepted values are:
              published and inactive.
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">boundingBox</td>
            <td className="govuk-table__cell">
              Limit results to fares data sets that contain information for the area within the
              rectangular boundingBox you set using co-ordinates: minLongitude, minLatitude,
              maxLongitude, maxLatitude.
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">limit</td>
            <td className="govuk-table__cell">The maximum number of records to return.</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">offset</td>
            <td className="govuk-table__cell">
              Return results that match the query starting from the specified offset. e.g.
              &amp;offset=10&amp;limit=25 returns results from 11 to 35. The default is set to 0.
            </td>
          </tr>
        </tbody>
      </table>

      <h2 data-qa="bus-header" className="govuk-heading-m">Bus location data API parameters</h2>
      <p className="govuk-body">
        Bus location data is provided within feeds. The metadata query parameters here will only
        return the bus location data that satisfies your chosen parameters.
      </p>
      <table className="govuk-table govuk-!-margin-bottom-9">
        <thead className="govuk-table__head">
          <tr className="govuk-table__row">
            <th scope="col" className="w-30-l govuk-table__header">Name</th>
            <th scope="col" className="govuk-table__header">Description</th>
          </tr>
        </thead>
        <tbody className="govuk-table__body">
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">boundingBox</td>
            <td className="govuk-table__cell">
              Limit results to bus location data with vehicle position within the rectangular
              bounding box you set using co-ordinates: minLongitude, minLatitude, maxLongitude,
              maxLatitude.
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">operatorRef</td>
            <td className="govuk-table__cell">
              Limit results to data feeds with the operatorRef. The National Operator Code is
              often used by publishers as the input for operatorRef, which can be found on the
              Traveline website,{' '}
              <a
                className="govuk-link"
                href="https://www.travelinedata.org.uk/traveline-open-data/transport-operations/about-2/"
                target="_blank"
                rel="noopener noreferrer"
              >
                https://www.travelinedata.org.uk/traveline-open-data/transport-operations/about-2/
              </a>
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">lineRef</td>
            <td className="govuk-table__cell">Limit results to bus location data with the specified Line Ref.</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">producerRef</td>
            <td className="govuk-table__cell">Limit results to bus location data with the specified Producer Ref.</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">originRef</td>
            <td className="govuk-table__cell">
              Limit results to bus location data with the specified Origin Ref. Inputs for Origin
              Ref are normally National Public Transport Access Nodes (NaPTAN), which can be
              found on the following website:{' '}
              <a
                className="govuk-link"
                href="https://data.gov.uk/dataset/ff93ffc1-6656-47d8-9155-85ea0b8f2251/national-public-transport-access-nodes-naptan"
                target="_blank"
                rel="noopener noreferrer"
              >
                https://data.gov.uk/dataset/ff93ffc1-6656-47d8-9155-85ea0b8f2251/national-public-transport-access-nodes-naptan
              </a>
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">destinationRef</td>
            <td className="govuk-table__cell">
              Limit results to bus location data with the specified Destination Ref. Inputs for
              Destination Ref are normally National Public Transport Access Nodes (NaPTAN), which
              can be found on the following website:{' '}
              <a
                className="govuk-link"
                href="https://data.gov.uk/dataset/ff93ffc1-6656-47d8-9155-85ea0b8f2251/national-public-transport-access-nodes-naptan"
                target="_blank"
                rel="noopener noreferrer"
              >
                https://data.gov.uk/dataset/ff93ffc1-6656-47d8-9155-85ea0b8f2251/national-public-transport-access-nodes-naptan
              </a>
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">vehicleRef</td>
            <td className="govuk-table__cell">
              Limit results to bus location data with the specified vehicleRef. The vehicleRef is
              a unique reference for the vehicle that is consistent and is generated by the
              vehicle equipment.
            </td>
          </tr>
        </tbody>
      </table>

      <h2 data-qa="bus-header" className="govuk-heading-m">GTFS RT-specific API parameters:</h2>
      <table className="govuk-table govuk-!-margin-bottom-9">
        <thead className="govuk-table__head">
          <tr className="govuk-table__row">
            <th scope="col" className="w-30-l govuk-table__header">Name</th>
            <th scope="col" className="govuk-table__header">Description</th>
          </tr>
        </thead>
        <tbody className="govuk-table__body">
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">routeId</td>
            <td className="govuk-table__cell">Limit results to bus location data with the specific routeId.</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">startTimeAfter</td>
            <td className="govuk-table__cell">Limit results to bus location data with a start time after startTimeAfter.</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">startTimeBefore</td>
            <td className="govuk-table__cell">Limit results to bus location data with a start time before startTimeBefore.</td>
          </tr>
        </tbody>
      </table>
    </>
  );
}

