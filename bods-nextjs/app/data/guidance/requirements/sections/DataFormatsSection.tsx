export function DataFormatsSection() {
  return (
    <>
      <h1 data-qa="formats-header" className="govuk-heading-l">Data formats</h1>
      <h1 data-qa="timetables-header" className="govuk-heading-l">Timetables</h1>
      <p className="govuk-body">
        Timetables data is available in the TransXChange format. This is an XML standard used
        for exchanging bus schedules and related data. More information including schema guidance
        can be found on the TransXChange website{' '}
        <a
          className="govuk-link dont-break-out"
          href="https://www.gov.uk/government/collections/transxchange"
          target="_blank"
          rel="noopener noreferrer"
        >
          https://www.gov.uk/government/collections/transxchange.
        </a>
      </p>
      <p className="govuk-body">
        Where multiple TransXChange datasets exist for an operator, you can use the
        RevisionNumber to understand the sequence of datasets that have been supplied. This can
        be used alongside StartDate and EndDate values to allow you to identify which data is
        valid at any one time, and how datasets continue on from each other.
      </p>
      <p className="govuk-body">
        A processed output of the timetables data is also made available in GTFS format for
        those consumers who would find it useful. The General Transit Feed Specification (GTFS)
        is a data specification that allows public transit agencies to publish their transit data
        in a format that can be consumed by a wide variety of software applications. Today, the
        GTFS data format is used by thousands of public transport providers. More information on
        this can be{' '}
        <a className="govuk-link" href="https://gtfs.org/" target="_blank" rel="noopener noreferrer">
          found here
        </a>.
      </p>

      <h1 data-qa="fares-header" className="govuk-heading-l">Fares data</h1>
      <p className="govuk-body">
        Fares data is available in the NeTEx format. This is an XML standard developed during
        2019 by industry standard leads to provide an interoperable format for the publication of
        fares data within the UK bus industry. NeTEx is a CEN standard that can be used to
        represent many aspects of a multi-modal transport network. The UK profile includes the
        elements related to fares for buses, for more information on the schema and profile use
        the following links:
      </p>
      <p className="govuk-body">
        <a className="govuk-link dont-break-out" href="http://netex.uk/farexchange/" target="_blank" rel="noopener noreferrer">
          http://netex.uk/farexchange/
        </a>
      </p>
      <p className="govuk-body">
        <a
          className="govuk-link dont-break-out"
          href="http://www.transmodel-cen.eu/standards/netex/"
          target="_blank"
          rel="noopener noreferrer"
        >
          http://www.transmodel-cen.eu/standards/netex/
        </a>
      </p>

      <h1 data-qa="bus-header" className="govuk-heading-l">Bus location data</h1>
      <p className="govuk-body">
        Bus location data is available using the SIRI-VM profile shown in the table below. This
        is an XML standard for exchanging real time bus location information. More information
        including technical guidance on the SIRI-VM profile can be found{' '}
        <a
          className="govuk-link dont-break-out"
          href="https://www.gov.uk/government/publications/technical-guidance-publishing-location-data-using-the-bus-open-data-service-siri-vm"
          target="_blank"
          rel="noopener noreferrer"
        >
          here
        </a>.
      </p>
      <table className="govuk-table govuk-!-margin-bottom-9">
        <thead className="govuk-table__head">
          <tr className="govuk-table__row">
            <th scope="col" className="govuk-table__header last_updated_cell">SIRI-VM profile</th>
            <th scope="col" className="govuk-table__header">Type</th>
            <th scope="col" className="govuk-table__header">Mandatory in Profile</th>
            <th scope="col" className="govuk-table__header">Description</th>
          </tr>
        </thead>
        <tbody className="govuk-table__body">
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Produce ref</td>
            <td className="govuk-table__cell">xsd: NMTOKEN ref</td>
            <td className="govuk-table__cell">Yes</td>
            <td className="govuk-table__cell">Codespace for dataset producer.</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Vehicle Ref</td>
            <td className="govuk-table__cell">String</td>
            <td className="govuk-table__cell">Yes</td>
            <td className="govuk-table__cell">Reference to the Vehicle.</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">VehicleJourneyRef</td>
            <td className="govuk-table__cell"></td>
            <td className="govuk-table__cell">Yes</td>
            <td className="govuk-table__cell">Reference to the Vehicle journey.</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Operator ref</td>
            <td className="govuk-table__cell">xsd:NMTOKEN</td>
            <td className="govuk-table__cell">Yes</td>
            <td className="govuk-table__cell">
              Reference to Operator in question (ID to the corresponding company in the timetable
              data).
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Published line name</td>
            <td className="govuk-table__cell">Int</td>
            <td className="govuk-table__cell">Yes</td>
            <td className="govuk-table__cell">Published line name for the line the vehicle is running on.</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Line Ref</td>
            <td className="govuk-table__cell">xsd:NMTOKEN</td>
            <td className="govuk-table__cell">Yes</td>
            <td className="govuk-table__cell">
              Reference to the Line in question (ID to the corresponding object in the timetable
              data).
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Direction Ref</td>
            <td className="govuk-table__cell">String</td>
            <td className="govuk-table__cell">Yes</td>
            <td className="govuk-table__cell">Direction of the trip.</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Origin ref</td>
            <td className="govuk-table__cell"></td>
            <td className="govuk-table__cell">Yes</td>
            <td className="govuk-table__cell">Reference to the first stop on the vehicle&rsquo;s trip.</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Origin name</td>
            <td className="govuk-table__cell">xsd:string</td>
            <td className="govuk-table__cell">Yes</td>
            <td className="govuk-table__cell">
              Reference to origin Quay in question (ID to the corresponding Quay in the timetable
              data and national stop place registry).
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Aimed departure time</td>
            <td className="govuk-table__cell">xsd:dateTime</td>
            <td className="govuk-table__cell">Yes</td>
            <td className="govuk-table__cell">The schedule time of departure from the origin stop.</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Destination ref</td>
            <td className="govuk-table__cell">xsd:NMTOKEN</td>
            <td className="govuk-table__cell">Yes</td>
            <td className="govuk-table__cell">
              Reference to destination Quay in question (ID to the corresponding Quay in the
              timetable data and national stop place registry) NAPTAN stop.
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Destination name</td>
            <td className="govuk-table__cell">xsd:string</td>
            <td className="govuk-table__cell">Yes</td>
            <td className="govuk-table__cell">Name describing the destination of the departure.</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Aimed arrival time</td>
            <td className="govuk-table__cell">xsd:dateTime</td>
            <td className="govuk-table__cell">Yes</td>
            <td className="govuk-table__cell">The scheduled time of arrival at the destination stop.</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Vehicle Location-Longitude</td>
            <td className="govuk-table__cell">xsd:decimal</td>
            <td className="govuk-table__cell">Yes</td>
            <td className="govuk-table__cell">Longitude (-180 to 180).</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Vehicle Location-Latitude</td>
            <td className="govuk-table__cell">xsd:decimal</td>
            <td className="govuk-table__cell">Yes</td>
            <td className="govuk-table__cell">Latitude (-90 to 90).</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Recorded at (/GPS timestamp)</td>
            <td className="govuk-table__cell">xsd:dateTime</td>
            <td className="govuk-table__cell">Yes</td>
            <td className="govuk-table__cell">
              Timestamp for when the dataset was created/published i.e.
              2004-12-17T09:30:47-05:00.
            </td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Speed</td>
            <td className="govuk-table__cell"></td>
            <td className="govuk-table__cell">Yes</td>
            <td className="govuk-table__cell">Speed of the vehicle in question.</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Bearing</td>
            <td className="govuk-table__cell">xsd:float</td>
            <td className="govuk-table__cell"></td>
            <td className="govuk-table__cell">Current compass bearing (direction of VehicleJourney).</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Block ref</td>
            <td className="govuk-table__cell">String</td>
            <td className="govuk-table__cell">Yes</td>
            <td className="govuk-table__cell">
              Reference to the block of the vehicle running as defined by the running boards.
            </td>
          </tr>
        </tbody>
      </table>
      <p className="govuk-body">
        A processed output of bus location data is also made available in GTFS-RT format for
        those who wish to consume it. GTFS Realtime is a feed specification that allows public
        transportation agencies to provide realtime updates about their fleet to application
        developers. It is an extension to GTFS (General Transit Feed Specification), an open data
        format for public transportation schedules and associated geographic information. GTFS
        Realtime was designed around ease of implementation, good GTFS interoperability and a
        focus on passenger information. More information on this can be{' '}
        <a
          className="govuk-link"
          href="https://developers.google.com/transit/gtfs-realtime"
          target="_blank"
          rel="noopener noreferrer"
        >
          found here
        </a>.
      </p>
    </>
  );
}

