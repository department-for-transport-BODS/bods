import { SingleJourneyMatchingLogic } from './SingleJourneyMatchingLogic';

const SIRI_MANDATORY_FIELDS = [
  'Bearing', 'LineRef', 'OperatorRef', 'RecordedAtTime', 'ResponseTimestamp',
  'VehicleJourneyRef', 'VehicleLocation (Lat, Long)', 'ProducerRef', 'DirectionRef',
  'BlockRef', 'PublishedLineName', 'ValidUntilTime', 'DestinationRef', 'OriginName',
  'OriginRef', 'VehicleRef',
];

const SIRI_PARTIAL_FIELDS = ['BlockRef', 'PublishedLineName', 'DestinationRef', 'OriginName', 'OriginRef'];

const SIRI_NON_COMPLIANT_FIELDS = [
  'Bearing', 'LineRef', 'OperatorRef', 'RecordedAtTime', 'ResponseTimestamp',
  'VehicleJourneyRef', 'VehicleLocation (Lat, Long)', 'ProducerRef', 'DirectionRef',
  'VehicleRef', 'ValidUntilTime',
];

function FieldList({ fields }: { fields: string[] }) {
  return (
    <ul className="govuk-list govuk-list--bullet">
      {fields.map((field) => <li key={field}>{field}</li>)}
    </ul>
  );
}

export function DataQualitySection() {
  return (
    <>
      <h1 data-qa="data-quality-header" className="govuk-heading-l">Data quality</h1>
      <table data-qa="requirements-table" className="govuk-table">
        <thead data-qa="requirements-table-header" className="govuk-table__head">
          <tr className="govuk-table__row">
            <th scope="col" className="govuk-table__header">Data required</th>
            <th scope="col" className="govuk-table__header">Data format required</th>
            <th scope="col" className="govuk-table__header">Method</th>
          </tr>
        </thead>
        <tbody className="govuk-table__body">
          <tr data-qa="timetable-row" className="govuk-table__row">
            <td className="govuk-table__cell">Timetable</td>
            <td className="govuk-table__cell">TransXChange Version 2.4 profile v1.1a</td>
            <td className="govuk-table__cell"><p className="govuk-body">Validation against TxC-PTI 1.1a profile</p><p className="govuk-body">Data Quality report</p></td>
          </tr>
          <tr data-qa="bus-location-row" className="govuk-table__row">
            <td className="govuk-table__cell">Bus location</td>
            <td className="govuk-table__cell">DfT BODS SIRI-VM profile</td>
            <td className="govuk-table__cell">Validation against DfT BODS SIRI-VM profile</td>
          </tr>
          <tr data-qa="basic-fares-row" className="govuk-table__row"><td className="govuk-table__cell">Basic fares</td><td className="govuk-table__cell">UK NeTEx 1.10</td><td className="govuk-table__cell">Validation against schema</td></tr>
          <tr data-qa="complex-fares-row" className="govuk-table__row"><td className="govuk-table__cell">Complex fares</td><td className="govuk-table__cell">UK NeTEx 1.10</td><td className="govuk-table__cell">Validation against schema</td></tr>
          <tr className="govuk-table__row"><td className="govuk-table__cell">Matching bus Location to timetables data</td><td className="govuk-table__cell">DfT BODS SIRI-VM profile and its corresponding TransXChange Version 2.4 TxC-PTI 1.1.a data</td><td className="govuk-table__cell">Validation against SIRI-VM PTI and data matching v1.1</td></tr>
        </tbody>
      </table>

      <p className="govuk-body">Data quality checks are provided on the data supplied to the service to help operators identify and understand issues within their data. The issues identified may prevent a data consumer using and sharing their data with passengers. High data quality is expected for all data published on the service. It reduces barriers to entry for innovators and consumers and enables trust between passengers and the public transport network.</p>

      <h2 className="govuk-heading-m">Timetables data</h2>
      <p className="govuk-body">TransXChange data undergoes two sets of checks. In the first validation stage, it is checked against the TxC 2.4 schema and the PTI profile v1.1. The TxC 2.4 schema is the basic data standard mandated by DfT, and the PTI profile v1.1 is an additional mandate that clarifies the standard and creates a common, unambiguous data format. Find out more about the <a className="govuk-link" href="https://pti.org.uk/system/files/files/TransXChange%20PTI%20Profile%20v1-1.pdf" target="_blank" rel="noopener noreferrer">differences between the TxC 2.4 schema and the PTI profile v1.1</a>.</p>
      <p className="govuk-body">From 31 December 2020, files non-compliant to the PTI profile 1.1 will be rejected upon submission.</p>
      <p className="govuk-body">The feedback from the first upload validation is provided to the user to share with their software suppliers. In the second review step, a further data quality check produces a report highlighting common errors. Some observations are critical and must be rectified; others are advisory and may be false positives. Operators should use these reports as suggested improvements to their timetable data.</p>

      <h2 className="govuk-heading-m">Bus location data</h2>
      <p className="govuk-body">SIRI-VM data is taken into a central AVL system, where it is harmonised to produce a consistent SIRI-VM 2.0 output of bus location data for open data consumers.</p>
      <p className="govuk-body">We have introduced a SIRI-VM validator to ensure the highest data standards are provided to consumers. The validator checks the schema and mandatory fields specified within the <a className="govuk-link" href="https://www.gov.uk/government/publications/technical-guidance-publishing-location-data-using-the-bus-open-data-service-siri-vm" target="_blank" rel="noopener noreferrer">DfT BODS profile</a>. If a feed fails the schema check it is put into an inactive status. The validator runs one randomised check per day, excluding buses running from 12am-5am, and checks 1000 packets or 10 minutes from a feed each day.</p>
      <p className="govuk-body">There will be no blocking of feeds as long as they are valid SIRI and do not fail the schema. BODS compliance tags show whether feeds are compliant, non-compliant or partially compliant using a 7-day rolling average.</p>
      <p className="govuk-body">A SIRI-VM feed is deemed &lsquo;compliant&rsquo; if all fields below are present more than 70% of the time for the last 7 days.</p>
      <FieldList fields={SIRI_MANDATORY_FIELDS} />
      <p className="govuk-body">A SIRI-VM feed is deemed &lsquo;partially compliant&rsquo; if all other mandatory fields are present but the following fields are missing more than 30% of the time in the last 7 days.</p>
      <FieldList fields={SIRI_PARTIAL_FIELDS} />
      <p className="govuk-body">A SIRI-VM feed is deemed &lsquo;non-compliant&rsquo; if the fields below are not present more than 70% of the time for the last 7 days. It can also be assigned a direct non-compliant status if any one of these fields falls under 45% population during daily validation.</p>
      <FieldList fields={SIRI_NON_COMPLIANT_FIELDS} />
      <p className="govuk-body">Other compliance statuses:</p>
      <ul className="govuk-list govuk-list--bullet"><li>Undergoing validation: used for newly added feeds in the first 24 hours and compliant feeds for the first 7 days.</li><li>Awaiting publisher review: used during the first 7 days after publishing if critical or noncritical fields have not been provided by more than 70% of vehicles.</li><li>Unavailable due to dormant feed: used when no vehicles have run for 7 consecutive days and the feed has repeatedly evaded validation.</li></ul>
      <p className="govuk-body"><b>New feed validation process:</b></p>
      <p id="new-feed-v-process" className="govuk-body">When a new feed is added to BODS it will be validated in the following way:</p>
      <ol className="govuk-list govuk-list--number"><li>24 hours after a new SIRI feed is added, the validator checks mandatory fields and sends an error report if necessary.</li><li>Over the subsequent 6 days, while data is flowing, it continues to run randomised daily checks.</li><li>After Day 7, a fresh automated check runs each day and assigns a compliance status on a 7-day rolling average.</li></ol>
      <p className="govuk-body"><b>Automated feed validation process:</b></p>
      <ol className="govuk-list govuk-list--number"><li>The validator runs one randomised check per day, excluding buses running from 12am-5am.</li><li>The validator checks 1000 packets or 10 minutes from a feed each day.</li><li>70% of vehicles must populate mandatory fields to avoid non-compliant or partially compliant status.</li><li>If non-compliant fields are less than 45% populated, the feed is automatically marked non-compliant.</li><li>If more than 45% are populated, the rolling average assigns the compliance status based on the last 7 days.</li></ol>

      <h2 className="govuk-heading-m">AVL to timetables matching</h2>
      <p className="govuk-body">Validation against the SIRI-VM-PTI profile takes place in three stages: schema validation, SIRI-VM-PTI compliance, and checking that SIRI-VM data matches the timetable TXC-PTI profile. Matching ensures that data can be used to produce predicted or calculated bus arrival times.</p>
      <p className="govuk-body">The matching validation combines timetable and location data. To help achieve this, equivalent SIRI-VM-PTI and TXC-PTI fields must use the same content as specified in the <a className="govuk-link" href="https://pti.org.uk/system/files/files/SIRI_VM_PTI_Data_Matching_v1-1.pdf" target="_blank" rel="noopener noreferrer">SIRI VM &amp; Data Matching profile</a>.</p>
      <p className="govuk-body">The data in both fields must be an absolute match of text and formatting.</p>
      <table className="govuk-table"><thead className="govuk-table__head"><tr className="govuk-table__row"><th scope="col" className="govuk-table__header">SIRI Field</th><th scope="col" className="govuk-table__header">TXC PTI Match</th></tr></thead><tbody className="govuk-table__body">{[
        ['LineRef', 'LineName'], ['OperatorRef', 'NationalOperatorCode'], ['DatedVehicleJourneyRef', 'TicketMachine/JourneyCode'], ['DirectionRef', 'JourneyPattern/Direction'], ['BlockRef', 'BlockNumber'], ['PublishedLineName', 'LineName'], ['DestinationRef', 'JourneyPatternTimingLink/To/StopPointRef'], ['OriginRef', 'JourneyPatternTimingLink/From/StopPointRef'],
      ].map(([siri, txc]) => <tr className="govuk-table__row" key={siri}><td className="govuk-table__cell">{siri}</td><td className="govuk-table__cell">{txc}</td></tr>)}</tbody></table>
      <p className="govuk-body"><b>Automated matching process and report</b></p>
      <p className="govuk-body">The matching validator runs a randomised collection each day, excluding buses running from 12am-5am, and tests 1000 sampled packets or 10 minutes against the complete TXC dataset published on BODS. The report is generated for each feed every Monday and provides an overall percentage score, granular field matching results, matching errors and dataset details.</p>
      <p className="govuk-body">Operators can download the overall matching score and four weeks of archived reports from the &lsquo;Review My Published data&rsquo; Bus location dashboard. Weekly feed scores and reports are available at feed level. <a className="govuk-link" href="https://pti.org.uk/system/files/files/SIRI_VM_PTI_Data_Matching_v1-1.pdf" target="_blank" rel="noopener noreferrer">Read more information on SIRI-VM PTI and Data matching</a>.</p>

      <SingleJourneyMatchingLogic />

      <h2 className="govuk-heading-m">Fares data</h2>
      <p className="govuk-body">
        NeTEx data is validated against its respective schemas to check that it is in the expected
        format. As this format is new to the UK, more data quality checks may be enabled over time.
      </p>
    </>
  );
}


