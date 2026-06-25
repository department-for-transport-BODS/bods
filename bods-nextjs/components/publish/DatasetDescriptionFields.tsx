import { ReactNode } from 'react';

type DatasetDescriptionFieldsProps = {
  description: string;
  shortDescription: string;
  descriptionLabel?: string;
  shortDescriptionLabel?: string;
  descriptionHint?: ReactNode;
  shortDescriptionHint?: ReactNode;
  maxShortDescLength?: number;
  descriptionClassName?: string;
  shortDescriptionClassName?: string;
  errors?: { description?: string; shortDescription?: string };
  onDescriptionChange: (value: string) => void;
  onShortDescriptionChange: (value: string) => void;
};

export function DatasetDescriptionFields({
  description,
  shortDescription,
  descriptionLabel = 'Data set description',
  shortDescriptionLabel = 'Dataset short description',
  descriptionHint,
  shortDescriptionHint,
  maxShortDescLength = 30,
  descriptionClassName,
  shortDescriptionClassName,
  errors,
  onDescriptionChange,
  onShortDescriptionChange,
}: DatasetDescriptionFieldsProps) {
  return (
    <>
      <div className={`govuk-form-group ${errors?.description ? 'govuk-form-group--error' : ''}`}>
        <label className="govuk-label" htmlFor="id_description">
          {descriptionLabel}
        </label>
        {descriptionHint && <div className="govuk-hint">{descriptionHint}</div>}
        {errors?.description && <p className="govuk-error-message">{errors.description}</p>}
        <textarea
          className={`govuk-textarea${descriptionClassName ? ` ${descriptionClassName}` : ''}`}
          id="id_description"
          rows={3}
          maxLength={300}
          value={description}
          onChange={(e) => onDescriptionChange(e.target.value)}
        />
      </div>
      <div className={`govuk-form-group ${errors?.shortDescription ? 'govuk-form-group--error' : ''}`}>
        <label className="govuk-label" htmlFor="id_short_description">
          {shortDescriptionLabel}
        </label>
        {shortDescriptionHint && <div className="govuk-hint">{shortDescriptionHint}</div>}
        {errors?.shortDescription && <p className="govuk-error-message">{errors.shortDescription}</p>}
        <input
          className={`govuk-input${shortDescriptionClassName ? ` ${shortDescriptionClassName}` : ''}`}
          id="id_short_description"
          type="text"
          maxLength={maxShortDescLength}
          value={shortDescription}
          onChange={(e) => onShortDescriptionChange(e.target.value)}
        />
        <span className="govuk-hint">
          You have {maxShortDescLength - shortDescription.length} characters remaining.
        </span>
      </div>
    </>
  );
}
