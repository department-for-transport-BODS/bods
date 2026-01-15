/**
 * Bus Location Data Section
 * Source: transit_odp/guidance/templates/guidance/bus_operators/buslocation.html
 */

export function BusLocationSection() {
  return (
    <>
      <h2 className="govuk-heading-l">Bus location data</h2>
      <p className="govuk-body">
        Operators must publish bus location data using the SIRI-VM Version 2.0 format.
        This data provides real-time information about the location of buses on the network.
      </p>
      <p className="govuk-body">
        The requirement date for bus location data was 7th January 2021.
      </p>

      <h2 className="govuk-heading-l">What is SIRI-VM?</h2>
      <p className="govuk-body">
        SIRI-VM (Service Interface for Real Time Information - Vehicle Monitoring) is
        the agreed standard for publishing real-time bus location data. This data
        enables passengers to see where their bus is and get accurate arrival predictions.
      </p>

      <h2 className="govuk-heading-l">AVL data feeds</h2>
      <p className="govuk-body">
        Automatic Vehicle Location (AVL) data feeds must be provided in SIRI-VM format.
        Most operators will work with their ETM (Electronic Ticket Machine) or real-time
        system supplier to provide this feed.
      </p>
    </>
  );
}


