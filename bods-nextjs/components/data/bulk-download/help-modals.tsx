import { DownloadHelpModal } from './DownloadHelpModal';

/**
 * Help modals shown next to the "Format" attribute on the download pages.
 * Source: transit_odp/browse/templates/browse/snippets/help_modals/{sirivm,gtfsrt,sirisx,netex}.html
 */

const SIRI_INTRO =
  'The Service Interface for Real-time Information (SIRI) specifies a European interface standard for exchanging information about the planned, current or projected performance of real-time public transport operations between different computer systems. The latest UK profile of SIRI can be found';

export function SiriVmHelp() {
  return (
    <DownloadHelpModal heading="SIRI-VM">
      <p className="govuk-body">
        {SIRI_INTRO}{' '}
        <a
          className="govuk-link"
          rel="noopener noreferrer"
          target="_blank"
          href="https://www.gov.uk/government/publications/technical-guidance-publishing-location-data-using-the-bus-open-data-service-siri-vm/technical-guidance-siri-vm"
        >
          here
        </a>
        .
      </p>
    </DownloadHelpModal>
  );
}

export function SiriSxHelp() {
  return (
    <DownloadHelpModal heading="SIRI-SX">
      <p className="govuk-body">
        {SIRI_INTRO}{' '}
        <a
          className="govuk-link"
          rel="noopener noreferrer"
          target="_blank"
          href="http://siri.org.uk/schema/schemas.htm"
        >
          here
        </a>
        .
      </p>
    </DownloadHelpModal>
  );
}

export function GtfsRtHelp() {
  return (
    <DownloadHelpModal heading="GTFS-RT">
      <p className="govuk-body">
        GTFS Realtime is a feed specification that allows public transportation agencies to provide
        realtime updates about their fleet to application developers. It is an extension to GTFS
        (General Transit Feed Specification), an open data format for public transportation
        schedules and associated geographic information.
      </p>
      <p className="govuk-body">
        To learn more about GTFS-RT please visit{' '}
        <a
          className="govuk-link"
          href="https://developers.google.com/transit/gtfs-realtime"
          target="_blank"
          rel="noopener noreferrer"
        >
          here
        </a>
        .
      </p>
    </DownloadHelpModal>
  );
}

export function NetexHelp() {
  return (
    <DownloadHelpModal heading="NeTEx">
      <p className="govuk-body">
        NeTEx provides a means to exchange data for passenger information such as stops, routes
        timetables and fares, among different computer systems, together with related operational
        data. It can be used to collect and integrate data from many different stakeholders, and to
        reintegrate it as it evolves through successive versions.
      </p>
      <p className="govuk-body">
        More information on this can be{' '}
        <a className="govuk-link" href="http://netex.uk/netex/schema.htm" target="_blank">
          found here
        </a>
        .
      </p>
    </DownloadHelpModal>
  );
}
