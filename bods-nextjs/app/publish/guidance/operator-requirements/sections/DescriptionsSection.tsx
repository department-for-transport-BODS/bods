/**
 * Writing data descriptions Section
 * Source: transit_odp/guidance/templates/guidance/bus_operators/descriptions.html
 */

export function DescriptionsSection() {
  return (
    <>
      <h1 data-qa="descriptions-header" className="govuk-heading-l">Writing data descriptions</h1>
      <p data-qa="descriptions-paragraph" className="govuk-body">
        All data uploaded to the service requires a data description. This description will be
        publicly available, so please do not use any personal information. Include an explanation
        of what data is included so data consumers know what they can expect at a high level.
        Explain why the data has been split into different data sets, for example by
        location/regions, operating companies or lines. Additional information depends on the
        type of data provided: a fares description could include the fare products,
        elicitabilities, travel documents and other information included within the data.
      </p>
    </>
  );
}


