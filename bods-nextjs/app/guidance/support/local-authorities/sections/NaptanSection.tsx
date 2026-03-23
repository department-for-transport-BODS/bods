import { config } from '@/config';

export function NaptanSection() {
  return (
    <>
      <h1 className="govuk-heading-l">NaPTAN stop data</h1>
      <p className="govuk-body">
        The Bus Open Data Regulations include a statutory requirement for local transport
        authorities to maintain and update data in the National Public Transport Access Node
        (NaPTAN) dataset for bus stops and stations. In practice, this means data staff at the
        local transport authorities will need to update the Department for Transport database
        when new bus stops are added, temporary stops are added or bus stops are either moved or
        removed.
      </p>
      <p className="govuk-body">
        Local transport authorities will also have a statutory duty to ensure that the National
        Public Transport Access Nodes (NaPTAN) data is accurate and up to date for their local
        area. Many local transport authorities are already voluntarily fulfilling this role
        however the Public Service Vehicle Open Data Regulations will now mandate this data to be
        provided from 07 January 2020 and no later than 31 December 2020. The Department for
        Transport would strongly encourage local transport authorities to begin reviewing their
        NaPTAN datasets and addressing any data quality issues, before the requirements come into
        effect next year.
      </p>
      <h2 className="govuk-heading-l">DfT support</h2>
      <p className="govuk-body">
        In preparation of the statutory requirements that will be coming into action next year,
        the DfT is offering a free service whereby local authorities can get in contact with{' '}
        <a className="govuk-link" href={`mailto:${config.supportEmail}`}>{config.supportEmail}</a>, to request
        a spreadsheet that contains potential NaPTAN corrections for the areas that you are
        responsible for.
      </p>
      <p className="govuk-body">
        The potential corrections involve a three-step process: (1) cross referencing the NaPTAN
        database with Passengers Bus Stop Checker and looking for differences in the bearing
        data; (2) the algorithm then interacts with Google APIs to further check street names;
        and (3) a manual sample is performed, removing any potential corrections that are likely
        due to naming conventions from different sources of data rather than improvements to the
        dataset.
      </p>
    </>
  );
}

