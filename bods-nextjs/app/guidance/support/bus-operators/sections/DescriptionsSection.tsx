/**
 * Writing data descriptions Section
 * Source: transit_odp/guidance/templates/guidance/bus_operators/descriptions.html
 */

export function DescriptionsSection() {
  return (
    <>
      <h2 className="govuk-heading-l">Writing data descriptions</h2>
      <p className="govuk-body">
        When publishing data, operators should provide clear and helpful descriptions
        that enable data consumers to understand what the data set contains.
      </p>
      <p className="govuk-body">
        Good descriptions should include:
      </p>
      <ul className="govuk-list govuk-list--bullet">
        <li>The geographic area covered by the data</li>
        <li>The type of services included</li>
        <li>Any specific routes or lines</li>
        <li>The time period the data covers</li>
      </ul>
    </>
  );
}


