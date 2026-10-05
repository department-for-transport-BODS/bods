'use client';

import { useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import 'air-datepicker/air-datepicker.css';
import { queryWith } from './query';

const DATE_PATTERN = /^(0[1-9]|[12][0-9]|3[01])\/(0[1-9]|1[012])\/(19|20)\d{2}$/;

function toIsoDate(date: Date): string {
  return `${date.getFullYear()}-${`0${date.getMonth() + 1}`.slice(-2)}-${`0${date.getDate()}`.slice(-2)}`;
}

// Source: transit_odp/publish/templates/publish/dataset_detail/timetable_filters.html
// Behaviour: initDatePicker / changeTargetDate in transit_odp/frontend/assets/js/timetable.js
export function TimetableDateFilter({ currDate }: { currDate: string }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const input = inputRef.current;
    if (!input) return;
    let destroyed = false;
    let picker: { destroy: () => void } | undefined;

    Promise.all([import('air-datepicker'), import('air-datepicker/locale/en')]).then(
      ([{ default: AirDatepicker }, { default: localeEn }]) => {
        if (destroyed) return;
        picker = new AirDatepicker(input, {
          locale: localeEn,
          dateFormat: 'dd/MM/yyyy',
          selectedDates: [new Date(currDate)],
          buttons: [
            { content: 'Exit', onClick: (dp) => dp.hide() },
            { content: 'Today', onClick: (dp) => dp.update({ selectedDates: [new Date()] }) },
          ],
          navTitles: { days: 'MMMM yyyy', months: 'yyyy', years: 'yyyy1 - yyyy2' },
          onSelect: ({ datepicker }) => datepicker.hide(),
        });
      },
    );

    return () => {
      destroyed = true;
      picker?.destroy();
    };
  }, [currDate]);

  const applyFilter = () => {
    const value = inputRef.current?.value ?? '';
    if (!DATE_PATTERN.test(value)) return;
    const [day, month, year] = value.split('/').map(Number);
    router.push(queryWith(searchParams, { date: toIsoDate(new Date(year, month - 1, day)) }));
  };

  return (
    <>
      {/* Django wraps this in {% flag is_complete_service_pages_active %} unquoted, so waffle resolves
          the name as a template variable and the "Timetable" branch always renders. */}
      <h2 className="govuk-heading-m">Timetable</h2>
      <h2 className="govuk-heading-m">Filter by</h2>
      <div className="govuk-form-group govuk-!-width-one-quarter govuk-!-padding-0">
        <label className="govuk-label" htmlFor="timetable_date">
          Date
        </label>
        <span id="timetable_date_hint" className="govuk-hint">
          For example: 21/11/2014
        </span>
        <div className="flex-container flexfill">
          <input
            ref={inputRef}
            type="text"
            id="timetable_date"
            name="start"
            className="w-90-l govuk-input"
            aria-describedby="timetable_date_hint"
            defaultValue={currDate}
          />
          {/* eslint-disable-next-line @next/next/no-img-element -- static 20px icon, mirrors Django markup */}
          <img
            id="timetable_date_calendar"
            className="govuk-!-margin-right-1 shifted-text"
            width={20}
            height={20}
            src="/assets/images/calendar-icon.png"
            alt="calendar-icon"
          />
        </div>
        <button type="submit" className="govuk-button govuk-!-margin-top-2" data-module="govuk-button" onClick={applyFilter}>
          Apply Filter
        </button>
      </div>
    </>
  );
}
