import Link from 'next/link';
import { publishAppPath, wwwPath } from '@/config/client';
import { useSupportConfig } from '@/components/shared/SupportConfigProvider';

export function MaintainingQualityDataSection() {
  const { ptiPdfUrl } = useSupportConfig();

  return (
    <>
      <h1 data-qa="api-ref-header" className="govuk-heading-l">Maintaining quality data</h1>
      <p className="govuk-body">
        The Bus Open Data Service is committed to ensuring the most robust quality of data is
        available on BODS. As of such we take special care in ensuring that high data quality is
        maintained through various ways as outlined below.
      </p>

      <h2 data-qa="all-data-header" className="govuk-heading-l">Timetables data</h2>
      <h3 data-qa="all-data-header" className="govuk-heading-m">BODS Compliant data</h3>
      <p className="govuk-body">
        Currently for timetables data, BODS mandates that all publishers produce timetables data
        in TransXChange 2.4 v1.1A PTI profile. This profile is an extension of general schema and
        makes certain fields mandatory, whilst clarifying the specific use of some other fields
        in TransXChange. The full PTI profile can be found here:
        <br />
        <a className="govuk-link" href={ptiPdfUrl} target="_blank" rel="noopener noreferrer">
          {ptiPdfUrl}
        </a>
      </p>
      <p className="govuk-body">
        The timetables data which is the above approved version is known as &lsquo;BODS Compliant
        data&rsquo; and is flagged as such in different parts of the Find Bus Open Data Service
        (including Browse, Download all, Data Catalogue and the API).
      </p>
      <h3 data-qa="all-data-header" className="govuk-heading-m">Data Quality reports and scoring</h3>
      <p className="govuk-body">
        Additionally, beyond the BODS Compliant tagging, BODS also does data quality checks which
        include key data-quality observations that would adversely impact the passenger
        experience, if unaddressed. The full list of checks can be found{' '}
        <Link className="govuk-link dont-break-out" href={publishAppPath('/guidance/data-quality-definitions')}>
          here
        </Link>.
      </p>
      <p className="govuk-body">
        BODS also generates a data quality score which can be seen as flagged in different parts
        of the Find Bus Open Data Service (including Browse, Changelog, Download all, Data
        Catalogue, and the API). The mechanism which the BODS algorithm uses to generate a data
        quality score can be found{' '}
        <Link className="govuk-link dont-break-out" href={publishAppPath('/guidance/score-description')}>
          here
        </Link>.
      </p>

      <h2 data-qa="all-data-header" className="govuk-heading-l">Fares data</h2>
      <p className="govuk-body">
        BODS will deliver new additions to the service to ensure publishers can perform data
        quality checks for fares data. The updates on this should be available to consumers via
        the Find Bus Open data site very soon. Please{' '}
        <Link className="govuk-link dont-break-out" href={wwwPath('/contact')}>contact us</Link> for any
        further queries on this.
      </p>

      <h2 data-qa="all-data-header" className="govuk-heading-l">Bus location data</h2>
      <p className="govuk-body">
        SIRI-VM data is taken into a central AVL system, where it is harmonised to produce a
        consistent SIRI-VM 2.0 output of bus location data for open data consumers.
      </p>
      <p className="govuk-body">
        We have introduced a SIRI-VM validator to BODS to ensure the highest data standards are
        provided to consumers. The validator has two parts: one that checks first for the schema
        and the second part checks for mandatory fields specified within the{' '}
        <a
          className="govuk-link dont-break-out"
          href="https://www.gov.uk/government/publications/technical-guidance-publishing-location-data-using-the-bus-open-data-service-siri-vm"
          target="_blank"
          rel="noopener noreferrer"
        >
          DfT BODS profile
        </a>. For the schema check, if the feed fails it, the feed will be put in an
        &lsquo;inactive&rsquo; status. The validator will check 250 packets from a feed each day.
      </p>
      <p className="govuk-body">
        Given the level of industry readiness in terms of providing consistent SIRI-VM data,
        there will be no blocking of feeds as long as they are valid SIRI (and don&apos;t fail
        the schema). However BODS compliance tags will be attached to showcase if they are:
        &lsquo;compliant&rsquo;, &lsquo;non-compliant&rsquo; or &lsquo;partially compliant&rsquo;
        using a 7-day rolling average. The validator will look at the last 7 days&apos; worth of
        SIRI-VM aggregate data and assign a compliance status accordingly.
      </p>
      <p className="govuk-body">
        A SIRI-VM feed will be deemed &lsquo;compliant&rsquo; if all fields here are present more
        than 70% of the time for the last 7 days.
      </p>
      <ul className="govuk-list govuk-list--bullet">
        <li>Bearing</li>
        <li>LineRef</li>
        <li>OperatorRef</li>
        <li>RecordedAtTime</li>
        <li>ResponseTimestamp</li>
        <li>VehicleJourneyRef</li>
        <li>VehicleLocation (Lat, Long)</li>
        <li>ProducerRef</li>
        <li>DirectionRef</li>
        <li>BlockRef</li>
        <li>PublishedLineName</li>
        <li>ValidUntilTime</li>
        <li>DestinationRef</li>
        <li>OriginName</li>
        <li>OriginRef</li>
        <li>VehicleRef</li>
      </ul>
      <p className="govuk-body">
        A SIRI-VM feed will be deemed &lsquo;partially compliant&rsquo; if it has all other
        mandatory fields present but only have the following fields below missing 70% of the time
        in the last 7 days.
      </p>
      <ul className="govuk-list govuk-list--bullet">
        <li>BlockRef</li>
        <li>PublishedLineName</li>
        <li>DestinationRef</li>
        <li>OriginName</li>
        <li>OriginRef</li>
      </ul>
      <p className="govuk-body">
        A SIRI-VM feed will be deemed &lsquo;non-compliant&rsquo; if all fields below are not
        present more than 70% of the time for the last 7 days. It can also be assigned a direct
        non-compliant status if any one of the fields below fall under 45% population at the time
        of the daily validation check. This is because this would count as a gross error in the
        data and would be highlighted to the publisher right away.
      </p>
      <ul className="govuk-list govuk-list--bullet">
        <li>Bearing</li>
        <li>LineRef</li>
        <li>OperatorRef</li>
        <li>RecordedAtTime</li>
        <li>ResponseTimestamp</li>
        <li>VehicleJourneyRef</li>
        <li>VehicleLocation (Lat, Long)</li>
        <li>ProducerRef</li>
        <li>DirectionRef</li>
        <li>VehicleRef</li>
        <li>ValidUntilTime</li>
      </ul>
      <p className="govuk-body">Other compliance statuses:</p>
      <ul className="govuk-list govuk-list--bullet">
        <li>
          Undergoing validation: This status will be used for all newly added feeds in the first
          24 hours until initial checks are completed. It will also be used for all compliant
          feeds for the first 7 days until the &lsquo;automated flow&rsquo; rolling validation
          logic becomes active.
        </li>
        <li>
          Awaiting publisher review: This status will be used for all feeds in the first 7 days
          after publishing if a critical or noncritical fields(s) has not been provided by &gt;70%
          of vehicles in a daily check.
        </li>
        <li>
          Unavailable due to dormant feed: This status will be used for all feeds which
          don&rsquo;t have any vehicles running for 7 consecutive days and henceforth have
          repeatedly evaded validation.
        </li>
      </ul>
      <p className="govuk-body govuk-!-font-weight-bold">New feed validation process:</p>
      <p className="govuk-body">
        When a new feed is added to BODS it will be validated in the following way:
      </p>
      <ol className="govuk-list govuk-list--number">
        <li>
          24 hours after a new SIRI feed is added the validator will check against the mandatory
          fields and if necessary, an error report will be sent to operators.
        </li>
        <li>
          Over the subsequent 6 days when data is flowing through it will continue to run
          randomised daily checks.
        </li>
        <li>
          After Day 7: each day a fresh automated validation check will run and a compliance
          status will be assigned on a 7-day rolling average.
        </li>
      </ol>
      <p className="govuk-body govuk-!-font-weight-bold">Automated feed validation process:</p>
      <ol className="govuk-list govuk-list--number">
        <li>The validator will run 1 randomised check per day (excluding buses running from 12am-5am).</li>
        <li>The validator will check 250 packets from a feed each day.</li>
        <li>
          70% of vehicles on the feed need to be populating the mandatory fields to avoid moving
          in to non/partial compliance error status (e.g that means 70% of &lsquo;Bearing&rsquo;
          should be present in the last 7 days&rsquo; worth of data, if not, it will move to a
          non-compliant status).
        </li>
        <li>
          If the daily check has any non-compliant fields which are less than 45% populated (for
          each non-compliant feed), it will automatically move the compliance status to
          &lsquo;non-compliant&rsquo; as it is a gross error.
        </li>
        <li>
          If the daily check has more than 45% of non-compliant fields populated (for each
          non-compliant feed), then the rolling average check will kick in and assign a
          compliance status based on the last 7 days.
        </li>
      </ol>
    </>
  );
}

