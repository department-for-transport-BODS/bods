import Link from 'next/link';
import { dataPath } from '@/config/client';
import { CatalogueDefinitionTable } from '../CatalogueDefinitionTable';
import {
  OVERALL_CATALOGUE_FIELDS,
  TIMETABLE_CATALOGUE_FIELDS,
  FARES_CATALOGUE_FIELDS,
  DISRUPTIONS_CATALOGUE_FIELDS,
  ORGANISATIONS_CATALOGUE_FIELDS,
  LOCATION_CATALOGUE_FIELDS,
  OPERATOR_NOC_CATALOGUE_FIELDS,
} from '../dataCatalogueDefinitions';

export function DataCatalogueSection() {
  return (
    <>
      <h1 data-qa="using-api-header" className="govuk-heading-l">Data Catalogue</h1>
      <p className="govuk-body">
        <Link className="govuk-link" href={dataPath('/catalogue')}>The data catalogue zip</Link>{' '}
        contains a series of CSVs which gives a machine-readable overview of all the data that
        resides in BODS currently.
      </p>
      <p className="govuk-body">
        Note that the data catalogue only covers the data from <b>primary data sources</b> on
        BODS which is timetables data in TransXChange format, bus location data in SIRI-VM format
        and fares data in NeTEx format. Other non-primary data on BODS (e.g GTFS converted forms)
        are not represented on the data catalogue.
      </p>
      <p className="govuk-body">The data catalogue zip contains 7 distinct CSVs:</p>
      <ul className="govuk-list govuk-list--bullet">
        <li>
          Overall data catalogue: this contains a high-level overview of all the static data on
          BODS: timetables and fares data.
        </li>
        <li>
          Timetables data catalogue: this contains a detailed granular view of the timetables
          data within BODS. It also contains a detailed mapping of the BODS timetables data with
          the data from the Office of the Traffic Commissioner (OTC).
        </li>
        <li>Fares data catalogue: this contains a detailed granular view of the fares data within BODS.</li>
        <li>
          Disruptions data catalogue: this contains a detailed view of all of the disruptions
          active and pending within BODS.
        </li>
        <li>Organisations data catalogue: this contains helpful counts of data at an organisation level.</li>
        <li>Location data catalogue: this contains an overview of the location data within BODS.</li>
        <li>
          Operator NOC data catalogue: this describes all organisations on BODS and the National
          Operator Codes (NOCs) that are associated with them.
        </li>
      </ul>
      <h2 className="govuk-heading-m">Field definitions:</h2>
      <p className="govuk-body">
        The data catalogue contains certain fields the definitions and explanations of which can
        be found below.
      </p>

      <h3 className="govuk-heading-s">Overall data catalogue:</h3>
      <CatalogueDefinitionTable fields={OVERALL_CATALOGUE_FIELDS} />

      <h3 className="govuk-heading-s">Timetables data catalogue:</h3>
      <CatalogueDefinitionTable fields={TIMETABLE_CATALOGUE_FIELDS} />

      <h3 className="govuk-heading-s">Fares data catalogue:</h3>
      <CatalogueDefinitionTable fields={FARES_CATALOGUE_FIELDS} />

      <h3 className="govuk-heading-s">Disruptions data catalogue:</h3>
      <CatalogueDefinitionTable fields={DISRUPTIONS_CATALOGUE_FIELDS} />

      <h3 className="govuk-heading-s">Organisations data catalogue:</h3>
      <CatalogueDefinitionTable fields={ORGANISATIONS_CATALOGUE_FIELDS} />

      <h3 className="govuk-heading-s">Location data catalogue:</h3>
      <CatalogueDefinitionTable fields={LOCATION_CATALOGUE_FIELDS} />

      <h3 className="govuk-heading-s">Operator NOC data catalogue:</h3>
      <CatalogueDefinitionTable fields={OPERATOR_NOC_CATALOGUE_FIELDS} />
    </>
  );
}

