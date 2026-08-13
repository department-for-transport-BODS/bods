/**
 * Timetables Data Section
 * Source: transit_odp/guidance/templates/guidance/bus_operators/timetables.html
 */

import { SupportEmailLink } from './SupportEmailLink';

export function TimetablesSection() {
  return (
    <>
      <h2 data-qa="timetables-header" className="govuk-heading-l">Timetables data requirement</h2>
      <p className="govuk-body">
        Operators will be expected to upgrade their systems/processes and upskill their staff
        to provide timetables data to the service in the TransXChange Version 2.4 from
        31st December 2020. The Bus Open Data Service is now ready for operators to start
        publishing their data.
      </p>

      <h2 data-qa="what-trans-header" className="govuk-heading-l">What is TransXChange?</h2>
      <p className="govuk-body">
        Timetables data must be published using TransXChange (TxC); the agreed industry
        standard for the publication of schedule data. Omnibus will launch a 2.4 validator
        and export in autumn 2020.
      </p>

      <h2 data-qa="produce-trans-header" className="govuk-heading-l">How can I produce TransXchange?</h2>
      <p className="govuk-body">
        Speak with your Local Transport Authority about the TransXChange data they can provide
        to you. Methods of producing TransXChange 2.4 include procuring scheduling
        software or using the free TxC 2.4 tool provided by DfT, from the following website:
      </p>
      <p className="govuk-body">
        <a className="govuk-link" rel="noopener noreferrer" target="_blank" href="https://www.gov.uk/guidance/publish-bus-open-data">
          https://www.gov.uk/guidance/publish-bus-open-data
        </a>
      </p>
      <p className="govuk-body">
        If you require additional support, DfT can support the creation of TxC using the
        tool. For more information please contact <SupportEmailLink />.
      </p>

      <h2 data-qa="block-number-header" className="govuk-heading-l">Block Number</h2>
      <p className="govuk-body">
        One of the fields within the timetables data is Block Number. Operators are encouraged
        to include the BlockNumber field in all their TransXChange 2.4 files as soon as this
        information becomes available to the operator because it enables data consumers to
        combine information from timetables and bus location data. This enables them to provide
        quality information to passengers. If it is not provided, partial matching methods are
        used, which reduces the quality of data that third parties can supply to passengers.
        It also reduces the number of data consumers willing to use the data within their apps
        and services. The corresponding object in the location data is BlockRef, often powered
        by running boards or driver duties.
      </p>

      <h2 data-qa="revision-number-header" className="govuk-heading-l">Revision number</h2>
      <p className="govuk-body">
        Use the RevisionNumber in your TransXChange file to indicate the TransXChange file you
        are replacing. It will be important to indicate to consumers of your data how to connect
        datasets and maintain version control. If multiple files are valid within a period the
        highest revision number should be considered the correct file.
      </p>

      <h2 data-qa="trans-profile-header" className="govuk-heading-l">TransXChange profile</h2>
      <p className="govuk-body">
        The guide is for technology suppliers (ETM and scheduling software) as well as operators.
        It provides an overview of how the TransXChange model works, a detailed description of
        the schema elements, worked examples and technical annexes, including a specification of
        the integrity rules used in TransXchange.
      </p>
      <p className="govuk-body">
        <a className="govuk-link" rel="noopener noreferrer" target="_blank" href="https://www.gov.uk/government/collections/transxchange">
          https://www.gov.uk/government/collections/transxchange
        </a>
      </p>
    </>
  );
}


