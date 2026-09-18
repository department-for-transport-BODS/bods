/**
 * Fares Data Section
 * Source: transit_odp/guidance/templates/guidance/bus_operators/fares.html
 */

export function FaresSection() {
  return (
    <>
      <h1 data-qa="fares-data-header" className="govuk-heading-l">Fares data</h1>
      <p className="govuk-body">During 2019 industry standard leads developed the UK NeTEx profile to standardise the publication of fares data within the UK bus industry. NeTEx is a highly interoperable CEN standard that can represent various aspects of multi-modal transport networks, including timetables and fares.</p>
      <h2 data-qa="netex-header" className="govuk-heading-l">How can I produce NeTEx?</h2>
      <p className="govuk-body">Operators can use the free Fare Data Build Tool to produce their own NeTEx. The tool can be found here:</p>
      <p className="govuk-body"><a className="govuk-link" rel="noopener noreferrer" target="_blank" href="https://fares-data.dft.gov.uk/">https://fares-data.dft.gov.uk/</a></p>
      <p className="govuk-body">Operators who have ETM suppliers can talk with them about hosted NeTEx solutions. A large proportion of fares data already resides within ETM systems and can be leveraged to provide NeTEx to BODS. There may be a need for additional product development, so ensure your needs are understood by your supplier.</p>
      <p className="govuk-body">For bespoke NeTEx tools, operators can input a start date in the future to make sure tickets are applicable for the relevant amount of time.</p>
      <h2 data-qa="easier-fare-header" className="govuk-heading-l">Easier fares</h2>
      <p className="govuk-body">Operators that maintain easy to understand fare structures can see benefits including increased usage of their data by consumers, greater exposure of fares information to passengers, improved third-party representation, increased public trust, increased patronage and easier revenue apportionment. Easier fares are endorsed by DfT, passengers and local transport authorities.</p>
      <h2 data-qa="netex-profile-header" className="govuk-heading-l">NeTEx profile</h2>
      <p className="govuk-body">The UK NeTEx profile remains open on the Bus Open Data Service to allow accurate representations of operators&rsquo; offerings. For more information on the UK profile and schema use these links:</p>
      <ul className="govuk-list app-list--nav govuk-!-font-size-19"><li><a className="govuk-link" rel="noopener noreferrer" target="_blank" href="http://netex.uk/farexchange/">http://netex.uk/farexchange/</a></li><li><a className="govuk-link" rel="noopener noreferrer" target="_blank" href="http://www.transmodel-cen.eu/standards/netex/">http://www.transmodel-cen.eu/standards/netex/</a></li></ul>
      <h2 data-qa="simple-fares-header" className="govuk-heading-l">Simple and complex fares</h2>
      <p className="govuk-body">Simple fare and ticket information means information about:</p>
      <ul className="govuk-list govuk-list--bullet"><li>adult single and return fares and tickets</li><li>child single and return fares and tickets</li><li>group fares and tickets</li><li>period tickets</li><li>single operator fares and tickets</li><li>multi-operator fares and tickets</li><li>zonal fares and tickets</li><li>the ways in which fares may be paid</li><li>which tickets can be purchased in advance and which can only be purchased on board</li><li>age restrictions</li><li>time restrictions</li></ul>
      <p className="govuk-body">Complex fare and ticket information means information about fares that vary depending on:</p>
      <ul className="govuk-list govuk-list--bullet"><li>the route taken</li><li>the duration of the journey</li><li>the type and number of passengers</li><li>the method of payment</li><li>the amount of subsequent travel undertaken in a given period</li><li>whether or not a discount or cap is applied to the fare</li></ul>
    </>
  );
}


