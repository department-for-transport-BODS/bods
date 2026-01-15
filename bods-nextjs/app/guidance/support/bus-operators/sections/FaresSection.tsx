/**
 * Fares Data Section
 * Source: transit_odp/guidance/templates/guidance/bus_operators/fares.html
 */

export function FaresSection() {
  return (
    <>
      <h2 className="govuk-heading-l">Fares data</h2>
      <p className="govuk-body">
        Operators must publish fares data using the UK NeTEx 1.10 format. There are two
        types of fares data that must be published:
      </p>
      <ul className="govuk-list govuk-list--bullet">
        <li>Basic fares - required from 7th January 2021</li>
        <li>Complex fares - required from 7th January 2023</li>
      </ul>

      <h2 className="govuk-heading-l">What is NeTEx?</h2>
      <p className="govuk-body">
        NeTEx (Network Timetable Exchange) is the agreed standard for publishing fares
        data. The UK has developed a specific profile (UK NeTEx 1.10) for bus fares data.
      </p>

      <h2 className="govuk-heading-l">Basic vs Complex fares</h2>
      <p className="govuk-body">
        <strong>Basic fares</strong> include single and return ticket prices for standard
        adult fares.
      </p>
      <p className="govuk-body">
        <strong>Complex fares</strong> include multi-operator tickets, period passes,
        concessionary fares, and other fare products.
      </p>
    </>
  );
}


