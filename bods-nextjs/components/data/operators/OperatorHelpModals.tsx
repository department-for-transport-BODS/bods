'use client';

/**
 * Help modals shown on the operator detail page.
 *
 * Source: transit_odp/publish/templates/publish/snippets/help_modals/
 *   operator_details_{overall,timetable,avl,fares}_require_attention.html
 *   licence_color_symbol_popup.html
 *
 * The licence compliance modal is exported for reuse by the licence pages.
 */

import { HelpModal } from '@/components/shared/HelpModal';

export function OverallRequireAttentionHelp() {
  return (
    <HelpModal heading="Overall services require attention score">
      <p className="govuk-body">
        Each active registered service that falls within the scope of the BODS legislation is reviewed and will
        require attention if any issues exist for that service.
      </p>
      <p className="govuk-body">
        The overall score will count a service that has at least one issue relating to either timetables, location
        data or fares.
      </p>
      <p className="govuk-body">
        A service will require attention if the data for timetables, fares or AVL is not published, is out of date,
        or has data matching issues. The compliance report provides the results for all checks that are done to help
        you to resolve the issues impacting that service.
      </p>
      <p className="govuk-body">
        Please review this page for additional information relating to the way we use the available data to measure
        compliance for each data type.
        <br />
        <a
          href="https://data.bus-data.dft.gov.uk/guidance/requirements/?section=datacatalogue"
          target="_blank"
          className="govuk-link"
        >
          https://data.bus-data.dft.gov.uk/guidance/requirements/?section=datacatalogue
        </a>
      </p>
    </HelpModal>
  );
}

export function TimetableRequireAttentionHelp() {
  return (
    <HelpModal heading="Compliance of timetables data">
      <p className="govuk-body">
        The timetables data for each service is assessed to review the health and compliance in the following ways:
      </p>
      <p className="govuk-body">
        <b>Completeness</b> - is the data published?
      </p>
      <p className="govuk-body">
        <b>Timeliness</b> - is the data up to date in the following ways:
      </p>
      <ol className="govuk-list govuk-list--number govuk-!-margin-left-5">
        <li>Has an appropriate validity period for at least the next 42 days?</li>
        <li>Has been updated within the last 12 months?</li>
        <li>Has been updated to reflect changes made to the registration authority for that service?</li>
      </ol>
      <p className="govuk-body">
        <b>Data Quality</b> - Are there any critical data quality issues relating to this service?
      </p>
    </HelpModal>
  );
}

export function AvlRequireAttentionHelp() {
  return (
    <HelpModal heading="Compliance of real time data">
      <p className="govuk-body">
        The real-time data for each service is assessed to review the health and compliance in the following ways:
      </p>
      <p className="govuk-body">
        <b>Completeness</b> - is the data published?
      </p>
      <p className="govuk-body">
        <b>Accuracy</b> - Real time data published to BODS is used by a diverse set of consumers that rely on
        &apos;ready to match&apos;, high quality data, using three key elements:
      </p>
      <ol className="govuk-list govuk-list--number govuk-!-margin-left-5">
        <li>National Operator code.</li>
        <li>Line ref.</li>
        <li>Dated vehicle journey ref.</li>
      </ol>
      <p className="govuk-body">
        The matching report ensures that all consumers can easily use these three elements to confidently present real
        time data directly to passengers.
      </p>
      <p className="govuk-body">
        Existing journey planners, the BODS GTFS-RT output, and ABODS are highly engineered to overcome matching issues
        that are present in the data using additional data elements.
      </p>
      <p className="govuk-body">
        The purpose of this report is to highlight cases where matching requires additional engineering steps that are
        beyond the three key elements listed.
      </p>
      <p className="govuk-body">
        Please contact your supplier or our helpdesk to resolve the cases identified within the report.
      </p>
    </HelpModal>
  );
}

export function FaresRequireAttentionHelp() {
  return (
    <HelpModal heading="Compliance of fares data">
      <p className="govuk-body">
        The fares data for each service is assessed to review the health and compliance in the following ways:
      </p>
      <p className="govuk-body">
        <b>Completeness</b> - is the data published?
      </p>
      <p className="govuk-body">
        <b>Timeliness</b> - is the data up to date in the following ways:
      </p>
      <ol className="govuk-list govuk-list--number govuk-!-margin-left-5">
        <li>Has an appropriate validity period for at least the next 42 days?</li>
        <li>Has been updated within the last 12 months?</li>
      </ol>
      <p className="govuk-body">
        <b>Compliance</b> - is the data that has been published compliant with the validation logic?
      </p>
    </HelpModal>
  );
}

export function LicenceComplianceHelp({ nonCompliant }: { nonCompliant: boolean }) {
  return (
    <HelpModal
      heading="Licence colour indicates compliance"
      icon={
        <span className="help-icon compliance-indicator-help-icon">
          <span className={`compliance-indicator ${nonCompliant ? 'non-compliant' : 'compliant'}`} />
        </span>
      }
    >
      <p className="govuk-body">
        The red or green symbol indicates whether the data for each in scope and in season service associated with
        that licence is compliant. The symbol will be red if a service belonging to that licence is not compliant. The
        symbol will be green if all services belonging to that licence are compliant.
      </p>
    </HelpModal>
  );
}
