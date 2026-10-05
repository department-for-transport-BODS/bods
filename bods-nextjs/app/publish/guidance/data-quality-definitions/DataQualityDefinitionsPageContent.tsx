/**
 * Data quality observation definitions (glossary)
 *
 * Source: transit_odp/data_quality/templates/data_quality/definitions.html
 * View: transit_odp/data_quality/views/glossary.py - DataQualityGlossaryView
 */

'use client';

import { useEffect, useState } from 'react';
import { ExtraInfoTable, type ObservationDefinition } from '@/components/publish/data-quality/ExtraInfoTable';
import { ErrorSummary } from '@/components/shared';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { HOSTS, publishAppPath } from '@/config/client';
import { api } from '@/lib/api-client';
import { useTabs } from '@/hooks/useTabs';

type DefinitionCategory = {
  type: string;
  showCategory: boolean;
  observations: ObservationDefinition[];
};

type DefinitionLevel = {
  level: string;
  count: number;
  intro: string | null;
  categories: DefinitionCategory[];
};

type DefinitionsResponse = {
  levels: DefinitionLevel[];
};

const LEVEL_TEXT: Record<string, { tab: string; heading: string; intro?: string }> = {
  Critical: {
    tab: 'Critical observations',
    heading: 'Critical observations',
    intro:
      'These observations are considered critical in terms of data quality. An operator should aim to have zero critical observations in their data.',
  },
  Advisory: {
    tab: 'Advisory observations',
    heading: 'Advisory observations',
    intro:
      'These observations are considered advisory in terms of data quality and suggest there may be an issue in the data. Please review the issues and make the necessary corrections to resolve these if required.',
  },
  Feedback: { tab: 'Feedback', heading: 'Consumer Feedback' },
};

function ObservationAccordion({ observation }: { observation: ObservationDefinition }) {
  return (
    <details className="govuk-details govuk-!-margin-left-5">
      <summary className="govuk-details__summary">
        <span className="govuk-details__summary-text">{observation.title}</span>
        {!observation.isActive ? (
          <strong className="govuk-tag govuk-tag--grey govuk-!-margin-left-3 govuk-!-font-size-16">COMING SOON</strong>
        ) : null}
      </summary>
      <div className="govuk-details__text">
        <p className="govuk-body" dangerouslySetInnerHTML={{ __html: observation.text }} />
        {observation.extraInfo.length ? <ExtraInfoTable extraInfo={observation.extraInfo} /> : null}
        {observation.impacts ? (
          <>
            <h3 className="govuk-heading-s">Impacts</h3>
            <p className="govuk-body" dangerouslySetInnerHTML={{ __html: observation.impacts }} />
          </>
        ) : null}
      </div>
    </details>
  );
}

export default function DataQualityDefinitionsPageContent() {
  const [levels, setLevels] = useState<DefinitionLevel[] | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const { selectedTab, getTabProps, getPanelProps } = useTabs(levels?.map(({ level }) => level.toLowerCase()) ?? []);

  useEffect(() => {
    document.title = 'Observation definitions';
  }, []);

  useEffect(() => {
    let cancelled = false;
    api
      .get<DefinitionsResponse>('/api/publish/data-quality/definitions/')
      .then((data) => {
        if (cancelled) return;
        setLevels(data.levels);
      })
      .catch(() => {
        if (!cancelled) setErrorMessage('Unable to load the observation definitions. Please refresh and try again.');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="govuk-width-container">
      <Breadcrumbs
        items={[
          { label: 'Bus Open Data Service', href: HOSTS.www },
          { label: 'Publish Bus Open Data', href: HOSTS.publish },
          { label: 'Guidance', href: publishAppPath('/guidance') },
          {
            label: 'Observation definitions',
            href: publishAppPath('/guidance/data-quality-definitions'),
            current: true,
          },
        ]}
      />
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-full">
            <h1 className="govuk-heading-xl">Observation definitions</h1>
            <p className="govuk-body-m">Please find the definitions for the observations below.</p>
            <p className="govuk-body-m govuk-!-margin-bottom-6">
              <a
                className="govuk-link"
                href="https://www.gov.uk/government/collections/transxchange"
                target="_blank"
                rel="noopener noreferrer"
              >
                View Department for Transport&apos;s TransXChange Schema Guide
              </a>
            </p>
            {errorMessage ? <ErrorSummary errors={[errorMessage]} /> : null}
            {!levels && !errorMessage ? <p className="govuk-body">Loading...</p> : null}
            {levels?.length ? (
              <div className="govuk-tabs">
                <h2 className="govuk-tabs__title">Contents</h2>
                <ul className="govuk-tabs__list" role="tablist">
                  {levels.map(({ level }) => (
                    <li
                      key={level}
                      className={`govuk-tabs__list-item${selectedTab === level.toLowerCase() ? ' govuk-tabs__list-item--selected' : ''}`}
                      role="presentation"
                    >
                      <a
                        className="govuk-tabs__tab"
                        {...getTabProps(level.toLowerCase())}
                      >
                        {LEVEL_TEXT[level]?.tab ?? level}
                      </a>
                    </li>
                  ))}
                </ul>
                {levels.map((level) => {
                  const text = LEVEL_TEXT[level.level];
                  return (
                    <div
                      key={level.level}
                      className="govuk-tabs__panel"
                      {...getPanelProps(level.level.toLowerCase())}
                    >
                      <div className="govuk-!-padding-5">
                        <h2 className="govuk-heading-l">
                          {text?.heading ?? level.level} ({level.count})
                        </h2>
                        <p className="govuk-body">{text?.intro ?? level.intro}</p>
                        {level.categories.map((category) => (
                          <div key={category.type}>
                            {category.showCategory ? (
                              <h2 className="govuk-heading-l govuk-!-margin-bottom-3">{category.type}</h2>
                            ) : null}
                            {category.observations.map((observation) => (
                              <ObservationAccordion key={observation.title} observation={observation} />
                            ))}
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}
