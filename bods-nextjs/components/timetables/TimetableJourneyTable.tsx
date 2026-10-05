'use client';

import { Fragment, useEffect, useRef, type KeyboardEvent, type MouseEvent, type ReactNode } from 'react';
import Link from 'next/link';
import type { ReadonlyURLSearchParams } from 'next/navigation';
import type { TimetableDirection, TimetableObservation, TimetableRow } from './line-detail-types';
import { queryWith } from './query';

const RED = '#d4351c';

export type TooltipControls = {
  openId: string | null;
  toggle: (id: string) => void;
  close: () => void;
};

type Feedback = { url: string; searchParams: ReadonlyURLSearchParams } | null;

const stopClick = (event: MouseEvent) => event.stopPropagation();

function TooltipTrigger({
  tooltipId,
  controls,
  red,
  children,
}: {
  tooltipId: string;
  controls: TooltipControls;
  red?: boolean;
  children: ReactNode;
}) {
  const toggle = (event: MouseEvent) => {
    event.stopPropagation();
    controls.toggle(tooltipId);
  };
  const onKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.target === event.currentTarget && (event.key === 'Enter' || event.key === ' ')) {
      event.preventDefault();
      controls.toggle(tooltipId);
    }
  };

  return (
    <div
      className="tooltip govuk-link"
      style={red ? { color: RED } : undefined}
      title="More information"
      role="button"
      tabIndex={0}
      aria-expanded={controls.openId === tooltipId}
      aria-controls={tooltipId}
      onClick={toggle}
      onKeyDown={onKeyDown}
    >
      {children}
    </div>
  );
}

function tooltipClass(controls: TooltipControls, id: string) {
  return `tooltiptext${controls.openId === id ? ' showtooltip' : ''}`;
}

function CloseButton({ controls, id }: { controls: TooltipControls; id?: string }) {
  return (
    <button
      type="submit"
      className="govuk-button govuk-button--secondary govuk-!-margin-top-2 govuk-!-margin-bottom-1"
      id={id}
      data-module="govuk-button"
      onClick={controls.close}
    >
      Close
    </button>
  );
}

function FeedbackButton({ feedback, params }: { feedback: Feedback; params: Record<string, string> }) {
  if (!feedback) return null;
  return (
    <>
      <a
        href={`${feedback.url}${queryWith(feedback.searchParams, params)}`}
        className="govuk-button govuk-!-margin-top-2 govuk-!-margin-bottom-1"
      >
        Add Feedback
      </a>{' '}
    </>
  );
}

function ObservationAccordion({ observations, idPrefix }: { observations: TimetableObservation[]; idPrefix: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const root = ref.current;
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
    <div ref={ref} className="govuk-accordion" data-module="govuk-accordion" id="timetable_tooltip">
      {observations.map((observation, index) => (
        <div className="govuk-accordion__section" key={`${observation.title}-${index}`}>
          <div className="govuk-accordion__section-header">
            <span className="govuk-accordion__section-heading">
              <span className="govuk-accordion__section-button" id={`${idPrefix}-heading-${index + 1}`}>
                {observation.title}
              </span>
            </span>
          </div>
          <div
            id={`${idPrefix}-content-${index + 1}`}
            className="govuk-accordion__section-content govuk-!-padding-bottom-1 govuk-!-padding-top-0"
          >
            <p>{observation.text}</p>
            <p>{observation.resolve}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

function ColumnHeader({
  name,
  observation,
  tooltipId,
  direction,
  controls,
  feedback,
}: {
  name: string;
  observation: TimetableObservation | null;
  tooltipId: string;
  direction: string;
  controls: TooltipControls;
  feedback: Feedback;
}) {
  return (
    <TooltipTrigger tooltipId={tooltipId} controls={controls} red={name === '-'}>
      <div
        className={tooltipClass(controls, tooltipId)}
        style={{ width: observation ? 550 : 220 }}
        id={tooltipId}
        onClick={stopClick}
      >
        {observation ? (
          <div id="timetable_tooltip">
            <div>
              <span>
                <span className="govuk-!-font-weight-bold govuk-!-font-size-27">{observation.title}</span>
              </span>
            </div>
            <div className="govuk-!-font-weight-regular">
              <p>{observation.text}</p>
              <p>{observation.resolve}</p>
            </div>
          </div>
        ) : (
          <div id="timetable_tooltip">
            <div>
              <p>
                <span className="govuk-!-font-weight-bold">Journey Code:</span>{' '}
                <span className="govuk-!-font-weight-regular">{name}</span>
              </p>
            </div>
          </div>
        )}
        <FeedbackButton feedback={feedback} params={{ journey_code: name, direction }} />
        <CloseButton controls={controls} />
      </div>
      {name}
    </TooltipTrigger>
  );
}

function StopCell({
  row,
  direction,
  controls,
  feedback,
}: {
  row: TimetableRow;
  direction: string;
  controls: TooltipControls;
  feedback: Feedback;
}) {
  const { stop } = row;
  const tooltipId = `tooltip-${direction}-${row.index}`;
  const observation = stop.observation;
  const feedbackParams = { stop: stop.name, direction, atco_code: stop.atcoCode };
  const notInNaptan = observation?.title === 'Stop not found in NaPTAN' ? { color: RED } : undefined;

  return (
    <TooltipTrigger tooltipId={tooltipId} controls={controls} red={Boolean(observation)}>
      {stop.name}
      <p
        className={tooltipClass(controls, tooltipId)}
        style={observation ? { width: 550 } : undefined}
        id={tooltipId}
        onClick={stopClick}
      >
        {observation ? (
          <>
            <span className="govuk-!-font-weight-bold govuk-!-font-size-27">{observation.title}</span>
            <br />
            <br />
            <span>{observation.text}</span>
            <br />
            <br />
            <span>{observation.resolve}</span>
            <br />
            <br />
          </>
        ) : null}
        <span className="govuk-!-font-weight-bold" style={notInNaptan}>
          ATCO Code:&nbsp;
        </span>
        {observation ? <span style={notInNaptan}>{stop.atcoCode}</span> : stop.atcoCode}
        <br />
        <span className="govuk-!-font-weight-bold">Street:&nbsp;</span>
        {stop.street}
        <br />
        <span className="govuk-!-font-weight-bold">Indicator:&nbsp;</span>
        {stop.indicator}
        {observation?.title === 'Incorrect stop type' ? (
          <>
            <br />
            <span className="govuk-!-font-weight-bold text-color-red">Stop type:&nbsp;</span>
            <span className="text-color-red">{stop.stopType}</span>
          </>
        ) : null}
        <br />
        <FeedbackButton feedback={feedback} params={feedbackParams} />
        <CloseButton controls={controls} id={`closeToolTip-${direction}-${row.index}`} />
      </p>
    </TooltipTrigger>
  );
}

function TimeCell({
  departureTime,
  journeyId,
  observations,
  rowIndex,
  controls,
}: {
  departureTime: string;
  journeyId: number | null;
  observations: TimetableObservation[];
  rowIndex: number;
  controls: TooltipControls;
}) {
  if (!observations.length) return <span>{departureTime}</span>;

  const tooltipId = `${journeyId}-${rowIndex}`;
  return (
    <TooltipTrigger tooltipId={tooltipId} controls={controls} red>
      {departureTime}
      <div className={tooltipClass(controls, tooltipId)} style={{ width: 550 }} id={tooltipId} onClick={stopClick}>
        {observations.length > 1 ? (
          <ObservationAccordion observations={observations} idPrefix={`accordion-${tooltipId}`} />
        ) : (
          <div id="timetable_tooltip">
            {observations.map((observation, index) => (
              <Fragment key={`${observation.title}-${index}`}>
                <div>
                  <span>
                    <span className="govuk-!-font-weight-bold govuk-!-font-size-27">{observation.title}</span>
                  </span>
                </div>
                <div>
                  <p>{observation.text}</p>
                  <p>{observation.resolve}</p>
                </div>
              </Fragment>
            ))}
          </div>
        )}
        <CloseButton controls={controls} />
      </div>
    </TooltipTrigger>
  );
}

function PaginationArrow({ kind }: { kind: 'prev' | 'next' }) {
  return (
    <svg
      className={`govuk-pagination__icon govuk-pagination__icon--${kind}`}
      xmlns="http://www.w3.org/2000/svg"
      height="13"
      width="15"
      aria-hidden="true"
      focusable="false"
      viewBox="0 0 15 13"
    >
      <path
        d={
          kind === 'prev'
            ? 'm6.5938-0.0078125-6.7266 6.7266 6.7441 6.4062 1.377-1.449-4.1856-3.9768h12.896v-2h-12.984l4.2931-4.293-1.414-1.414z'
            : 'm8.107-0.0078125-1.4136 1.414 4.2926 4.293h-12.986v2h12.896l-4.1855 3.9766 1.377 1.4492 6.7441-6.4062-6.7246-6.7266z'
        }
      />
    </svg>
  );
}

// Source: transit_odp/publish/templates/publish/dataset_detail/timetable_journey_stop.html
// Tooltip behaviour: transit_odp/frontend/assets/js/tooltip.js
export function TimetableJourneyTable({
  details,
  searchParams,
  controls,
  feedbackUrl,
}: {
  details: TimetableDirection;
  searchParams: ReadonlyURLSearchParams;
  controls: TooltipControls;
  feedbackUrl: string | null;
}) {
  const { direction } = details;
  const feedback: Feedback = feedbackUrl ? { url: feedbackUrl, searchParams } : null;
  const narrow = details.columns.length <= 5;

  return (
    <>
      <table className={`govuk-table govuk-table--small-text-until-tablet${narrow ? ' timetables_govuk_table' : ''}`}>
        <caption className="govuk-table__caption govuk-table__caption--m">{details.journeyName}</caption>
        <thead className="govuk-table__head">
          <tr className="govuk-table__row">
            {details.columns.map((column, index) => (
              <th scope="col" className="govuk-table__header" key={`${column.name}-${index}`}>
                {index === 0 ? (
                  column.name
                ) : (
                  <ColumnHeader
                    name={column.name}
                    observation={column.observation}
                    tooltipId={`jc-${direction}-${index}`}
                    direction={direction}
                    controls={controls}
                    feedback={feedback}
                  />
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="govuk-table__body">
          {details.rows.map((row) => (
            <tr className="govuk-table__row" key={row.index}>
              <td className="govuk-table__cell timetable_govuk_body">
                <StopCell row={row} direction={direction} controls={controls} feedback={feedback} />
              </td>
              {row.cells.map((cell, index) => (
                <td className="govuk-table__cell timetable_govuk_body" key={`${cell.journeyId}-${index}`}>
                  <TimeCell
                    departureTime={cell.departureTime}
                    journeyId={cell.journeyId}
                    observations={cell.observations}
                    rowIndex={row.index}
                    controls={controls}
                  />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      <div className="govuk-grid-row">
        <div className="govuk-grid-column-one-half">
          <p className="govuk-body">
            {details.totalRowCount > 10 ? (
              <Link
                href={queryWith(searchParams, { [details.showAllParam]: details.showAll ? 'False' : 'True' })}
                className="govuk-link govuk-link--no-underline"
              >
                {details.showAll ? 'See less ' : 'See more '}
              </Link>
            ) : null}
          </p>
        </div>
        {details.totalPage > 0 ? (
          <div className="govuk-grid-column-one-half govuk-!-text-align-right">
            <nav
              className="govuk-pagination end-justified govuk-!-text-align-right govuk-!-width-full"
              role="navigation"
              aria-label="Pagination"
            >
              {details.currPage !== 1 ? (
                <div className="govuk-pagination__prev">
                  <Link
                    className="govuk-link govuk-pagination__link"
                    rel="prev"
                    href={queryWith(searchParams, { [details.pageParam]: String(details.currPage - 1) })}
                  >
                    <PaginationArrow kind="prev" />{' '}
                    <span className="govuk-pagination__link-title">
                      Previous
                      <br />
                      {details.currPage - 1} / {details.totalPage}{' '}
                      <span className="govuk-visually-hidden">page</span>
                    </span>
                  </Link>
                </div>
              ) : null}
              {details.currPage !== details.totalPage ? (
                <div className="govuk-pagination__next govuk-!-text-align-right">
                  <Link
                    className="govuk-link govuk-pagination__link"
                    rel="next"
                    href={queryWith(searchParams, { [details.pageParam]: String(details.currPage + 1) })}
                  >
                    <span className="govuk-pagination__link-title">
                      Next
                      <br />
                      {details.currPage + 1}/{details.totalPage}
                      <span className="govuk-visually-hidden">page</span>
                    </span>{' '}
                    <PaginationArrow kind="next" />
                  </Link>
                </div>
              ) : null}
            </nav>
          </div>
        ) : null}
      </div>
    </>
  );
}
