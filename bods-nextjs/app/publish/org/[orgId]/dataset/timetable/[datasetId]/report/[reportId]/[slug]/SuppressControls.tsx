'use client';

import { api } from '@/lib/api-client';

export type SuppressRequest = {
  serviceCode?: string;
  lineName?: string;
  rowId?: number | null;
  isSuppressed: boolean;
};

export function observationApiPath(orgId: string, datasetId: string, reportId: string, slug: string) {
  return `/api/publish/timetables/data-quality-report/${orgId}/${datasetId}/${reportId}/observations/${slug}/`;
}

export function suppressObservations(apiPath: string, body: SuppressRequest) {
  return api.post(`${apiPath}suppress/`, body);
}

export function SuppressAllButton({
  allSuppressed,
  disabled,
  onClick,
}: {
  allSuppressed: boolean;
  disabled?: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className="govuk-button govuk-button--secondary govuk-!-margin-0"
      data-module="govuk-button"
      disabled={disabled}
      onClick={onClick}
    >
      {allSuppressed ? 'Restore all observations' : 'Suppress all observations'}
    </button>
  );
}

export function SuppressCheckbox({
  id,
  checked,
  disabled,
  onChange,
}: {
  id: string;
  checked: boolean;
  disabled?: boolean;
  onChange: (checked: boolean) => void;
}) {
  return (
    <div className="govuk-form-group">
      <div className="govuk-checkboxes govuk-checkboxes--small" data-module="govuk-checkboxes">
        <div className="govuk-checkboxes__item">
          <input
            className="govuk-checkboxes__input"
            id={id}
            name="suppress"
            type="checkbox"
            checked={checked}
            disabled={disabled}
            onChange={(event) => onChange(event.target.checked)}
          />
          <label className="govuk-label govuk-checkboxes__label" htmlFor={id}>
            {checked ? 'Suppressed' : 'Suppress'}
          </label>
        </div>
      </div>
    </div>
  );
}
