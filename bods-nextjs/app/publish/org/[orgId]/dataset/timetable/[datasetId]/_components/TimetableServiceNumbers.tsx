'use client';

import { useEffect, useRef } from 'react';
import { publishAppPath } from '@/config/client';
import type { TimetableDistinctAttributes } from './timetableFeedDetailTypes';

interface TimetableServiceNumbersProps {
  orgId: number;
  datasetId: number;
  distinctAttributes: TimetableDistinctAttributes;
}

/**
 * "Review Service Numbers" accordion: licence number > NOC > line - service code.
 *
 * Source: transit_odp/publish/templates/publish/dataset_detail/review_service_codes.html
 */
export function TimetableServiceNumbers({ orgId, datasetId, distinctAttributes }: TimetableServiceNumbersProps) {
  const accordionRef = useRef<HTMLDivElement>(null);
  const detailPath = `/org/${orgId}/dataset/timetable/${datasetId}/detail`;

  useEffect(() => {
    const root = accordionRef.current;
    if (!root) return;
    import('govuk-frontend')
      .then(({ Accordion }) => {
        try {
          new Accordion(root);
        } catch {
          // Already initialised (React strict mode runs effects twice).
        }
      })
      .catch(() => undefined);
  }, []);

  return (
    <div>
      <h2 className="govuk-heading-l">Review Service Numbers</h2>
      <div ref={accordionRef} className="govuk-accordion" data-module="govuk-accordion" id="accordion-default">
        {Object.entries(distinctAttributes).map(([licenceNumber, nocs], licenceIndex) => (
          <div className="govuk-accordion__section" key={licenceNumber}>
            <div className="govuk-accordion__section-header">
              <h2 className="govuk-accordion__section-heading">
                <span className="govuk-accordion__section-button" id={`accordion-default-heading-${licenceIndex + 1}`}>
                  {licenceNumber}
                </span>
              </h2>
            </div>
            {Object.entries(nocs).map(([noc, lines], nocIndex) => (
              <div
                key={noc}
                id={`sub-accordion-content-${licenceIndex + 1}`}
                className="govuk-accordion__section-content"
                aria-labelledby={`sub-accordion-heading-${licenceIndex + 1}`}
              >
                <div className="govuk-accordion__section govuk-!-padding-left-7">
                  <div className="govuk-accordion__section-header">
                    <h2 className="govuk-accordion__section-heading">
                      <span className="govuk-accordion__section-button" id={`sub-accordion-heading-${nocIndex + 1}`}>
                        {noc}
                      </span>
                    </h2>
                  </div>
                  <div
                    id={`sub-accordion-content-${nocIndex + 1}`}
                    className="govuk-accordion__section-content"
                    aria-labelledby={`sub-accordion-heading-${nocIndex + 1}`}
                  >
                    {Object.entries(lines).flatMap(([lineName, serviceCodes]) =>
                      serviceCodes.map((serviceCode) => (
                        <p
                          key={`${lineName}-${serviceCode}`}
                          className="govuk-body govuk-!-margin-left-7 govuk-!-padding-bottom-3 border-bottom-custom"
                        >
                          <a
                            className="govuk-link"
                            href={publishAppPath(
                              `${detailPath}?${new URLSearchParams({ line: lineName, service: serviceCode }).toString()}`,
                            )}
                          >
                            {lineName} - {serviceCode}
                          </a>
                        </p>
                      )),
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
