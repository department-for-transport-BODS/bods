/**
 * Source: transit_odp/browse/templates/browse/timetables/dataset_detail/review_service_codes.html
 *
 * The element ids repeat Django's loop counters exactly (including the nested
 * `sub-accordion-content-<licence index>` quirk) so the markup stays identical.
 */

import Link from 'next/link';
import { dataPath } from '@/config/client';
import type { DatasetDetailLicence } from './types';

interface TimetableServiceNumbersProps {
  datasetId: number;
  licences: DatasetDetailLicence[];
}

function lineDetailHref(datasetId: number, lineName: string, serviceCode: string): string {
  const query = new URLSearchParams({ line: lineName, service: serviceCode });
  return dataPath(`/timetable/dataset/${datasetId}/detail?${query.toString()}`);
}

export function TimetableServiceNumbers({ datasetId, licences }: TimetableServiceNumbersProps) {
  return (
    <div>
      <h2 className="govuk-heading-l">Review Service Numbers</h2>
      <div className="govuk-accordion" data-module="govuk-accordion" id="accordion-default">
        {licences.map((licence, licenceIndex) => {
          const licenceCounter = licenceIndex + 1;
          return (
            <div className="govuk-accordion__section" key={licence.licenceNumber}>
              <div className="govuk-accordion__section-header">
                <h2 className="govuk-accordion__section-heading">
                  <span className="govuk-accordion__section-button" id={`accordion-default-heading-${licenceCounter}`}>
                    {licence.licenceNumber}
                  </span>
                </h2>
              </div>
              {licence.nocs.map((noc, nocIndex) => {
                const nocCounter = nocIndex + 1;
                return (
                  <div
                    key={noc.noc}
                    id={`sub-accordion-content-${licenceCounter}`}
                    className="govuk-accordion__section-content"
                    aria-labelledby={`sub-accordion-heading-${licenceCounter}`}
                  >
                    <div className="govuk-accordion__section govuk-!-padding-left-7">
                      <div className="govuk-accordion__section-header">
                        <h2 className="govuk-accordion__section-heading">
                          <span
                            className="govuk-accordion__section-button"
                            id={`sub-accordion-heading-${nocCounter}`}
                          >
                            {noc.noc}
                          </span>
                        </h2>
                      </div>
                      <div
                        id={`sub-accordion-content-${nocCounter}`}
                        className="govuk-accordion__section-content"
                        aria-labelledby={`sub-accordion-heading-${nocCounter}`}
                      >
                        {noc.lines.flatMap((line) =>
                          line.serviceCodes.map((serviceCode) => (
                            <p
                              key={`${line.lineName}-${serviceCode}`}
                              className="govuk-body govuk-!-margin-left-7 govuk-!-padding-bottom-3 border-bottom-custom"
                            >
                              <Link
                                className="govuk-link"
                                href={lineDetailHref(datasetId, line.lineName, serviceCode)}
                              >
                                {line.lineName} - {serviceCode}
                              </Link>
                            </p>
                          )),
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
}
