/**
 * Bus Location Data Section
 * Source: transit_odp/guidance/templates/guidance/bus_operators/buslocation.html
 */

const mandatoryFields = ['Bearing', 'BlockRef', 'DestinationRef', 'DirectionRef', 'LineRef', 'MonitoredVehicleJourney', 'OperatorRef', 'OriginName', 'OriginRef', 'ProducerRef', 'PublishedLineName', 'RecordedAtTime', 'ResponseTimestamp', 'ValidUntilTime', 'VehicleJourneyRef', 'VehicleLocation (Longitude, Latitude)', 'VehicleMonitoringDelivery (Vehicle Activity)'];
const optionalFields = ['Departure Boarding Activity', 'DestinationAimedArrivalTime', 'DestinationName', 'ItemIdentifier', 'MonitoredCall (Departure Boarding Activity)', 'Occupancy', 'OriginAimedDepartureTime', 'VehicleActivity', 'Velocity'];

export function BusLocationSection() {
  return (
    <>
      <h1 data-qa="bus-loc-header" className="govuk-heading-l">Bus location data</h1>
      <p className="govuk-body">Bus location data is also known as Automated Vehicle Location (AVL) and gives information about bus location at that point in time. All data feeds published must be in the SIRI-VM Version 2.0 or 2.0Q format.</p>
      <h2 data-qa="what-siri-header" className="govuk-heading-l">What is SIRI-VM?</h2>
      <p className="govuk-body">The Service Interface for Real Time Information (SIRI) specifies a European interface standard for exchanging information about the planned, current or projected performance of real-time public transport operations between computer systems.</p>
      <p className="govuk-body">SIRI-VM is specifically the vehicle monitoring service, which allows the exchange of real-time positions of public transport vehicles.</p>
      <p className="govuk-body">The service exchanges vehicle monitoring information between control systems and distributes it to journey planners, alert systems and displays. More information can be found at <a className="govuk-link" href="http://siri.org.uk/" target="_blank" rel="noopener noreferrer">http://siri.org.uk/</a>.</p>
      <h2 data-qa="how-siri-header" className="govuk-heading-l">How can I produce SIRI-VM?</h2>
      <p className="govuk-body">Operators with electronic ticket machine, location system or real-time suppliers should contact them to discuss their ability to provide a feed aligned with the Department for Transport SIRI-VM Profile.</p>
      <p className="govuk-body">Operators without ETM suppliers should contact their Local Transport Authority to discuss solutions, such as hardware lease agreements, and guidance they can offer.</p>
      <h2 data-qa="crowdedness-header" className="govuk-heading-l">Crowdedness data</h2>
      <p className="govuk-body">Information about crowdedness has become a key metric in passenger and modal decisions. Passengers need to assess safety by time of day and journey option. By providing clear crowdedness data, operators can balance safety and capacity and help potential passengers shift safely to local bus options. Operators are expected to include this information to support passenger safety.</p>
      <p className="govuk-body">The fields required for crowdedness data are:</p>
      <ul className="govuk-list govuk-list--bullet"><li>Monitored Vehicle Journey - Progress Info - Occupancy</li><li>Monitored Vehicle Journey - Departure Boarding Activity (to be used to set to No Boarding if the vehicle is full)</li></ul>
      <h2 data-qa="dft-profile-header" className="govuk-heading-l">The Department for Transport SIRI VM Profile</h2>
      <p className="govuk-body">The requirement for operators of local bus services across England to openly publish location data feeds to the Bus Open Data Service came into effect on 07 January 2021.</p>
      <p className="govuk-body">The table below gives an overview of the mandatory and optional elements included in the profile.</p>
      <table className="govuk-table"><thead className="govuk-table__head"><tr className="govuk-table__row"><th scope="col" className="govuk-table__header">Mandatory</th><th scope="col" className="govuk-table__header">Optional</th></tr></thead><tbody className="govuk-table__body">{mandatoryFields.map((field, index) => <tr className="govuk-table__row" key={field}><td className="govuk-table__cell">{field}</td><td className="govuk-table__cell">{optionalFields[index] || ''}</td></tr>)}</tbody></table>
      <p className="govuk-body"><a className="govuk-link" href="https://www.gov.uk/government/publications/technical-guidance-publishing-location-data-using-the-bus-open-data-service-siri-vm" target="_blank" rel="noopener noreferrer">Read the DfT BODS SIRI-VM technical guidance</a>.</p>
    </>
  );
}


