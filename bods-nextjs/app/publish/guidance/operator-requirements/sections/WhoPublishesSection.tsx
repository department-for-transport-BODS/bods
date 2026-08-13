/**
 * Who Must Publish Section
 * Source: transit_odp/guidance/templates/guidance/bus_operators/who_publish_data.html
 */

export function WhoPublishesSection() {
  return (
    <>
      <h2 data-qa="who-publish-heading" className="govuk-heading-l">
        Who must publish open data?
      </h2>
      <p data-qa="who-publish-paragraph" className="govuk-body">
        All operators who run public bus services in England must publish their data from
        late 2020. Community bus operators are currently outside the scope of the new service
        (i.e. those with exemptions under Section 19 or Section 22 of the Transport Act 1985).
      </p>
    </>
  );
}


