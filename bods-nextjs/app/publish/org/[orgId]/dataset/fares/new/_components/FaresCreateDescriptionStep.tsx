'use client';

import { FormEvent } from 'react';
import { FormButtons } from './FormButtons';

type DescriptionErrors = { description?: string; shortDescription?: string };

function fieldClass(base: string, error?: string) {
  return `govuk-!-width-three-quarters ${base}${error ? ` ${base}--error` : ''}`;
}

// Mirrors Django `FaresFeedDescriptionForm` as rendered by `fares/feed_form.html`.
export function FaresCreateDescriptionStep({
  description,
  shortDescription,
  errors,
  onDescriptionChange,
  onShortDescriptionChange,
  onSubmit,
  onCancel,
}: Readonly<{
  description: string;
  shortDescription: string;
  errors: DescriptionErrors;
  onDescriptionChange: (value: string) => void;
  onShortDescriptionChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onCancel: () => void;
}>) {
  return (
    <form method="post" onSubmit={onSubmit} noValidate>
      <h1 className="govuk-heading-xl">Describe your data set</h1>
      <div className={`govuk-form-group${errors.description ? ' govuk-form-group--error' : ''}`}>
        <label className="govuk-label" htmlFor="id_description-description">
          Data set description
        </label>
        <span id="id_description-description-hint" className="govuk-hint">
          This information will give context to data set users. Please be descriptive but do not include
          personally identifiable information. You may wish to include: The original file name, start date
          of data, description of the fares, products, OpCo, locations/region, routes/service numbers for
          which the data applies, or any other useful high level information. The description should reflect
          the data included at a high level.
        </span>
        {errors.description ? (
          <span id="1_id_description-description-error" className="govuk-error-message">
            {errors.description}
          </span>
        ) : null}
        <textarea
          id="id_description-description"
          name="description-description"
          className={fieldClass('govuk-textarea', errors.description)}
          rows={3}
          aria-describedby="id_description-description-hint"
          value={description}
          onChange={(event) => onDescriptionChange(event.target.value)}
        />
      </div>
      <div className={`govuk-form-group${errors.shortDescription ? ' govuk-form-group--error' : ''}`}>
        <label className="govuk-label" htmlFor="id_description-short_description">
          Data set short description
        </label>
        <span id="id_description-short_description-hint" className="govuk-hint">
          This info will be displayed on your published data set dashboard to identify this data set and will
          not be visible to data set users. The maximum number of characters (with spaces) is 30 characters.
        </span>
        {errors.shortDescription ? (
          <span id="1_id_description-short_description-error" className="govuk-error-message">
            {errors.shortDescription}
          </span>
        ) : null}
        <input
          type="text"
          id="id_description-short_description"
          name="description-short_description"
          className={fieldClass('govuk-input', errors.shortDescription)}
          maxLength={30}
          size={30}
          aria-describedby="id_description-short_description-hint"
          value={shortDescription}
          onChange={(event) => onShortDescriptionChange(event.target.value)}
        />
      </div>
      <FormButtons onCancel={onCancel} />
    </form>
  );
}
