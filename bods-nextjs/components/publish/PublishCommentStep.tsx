'use client';

import type { FormEvent } from 'react';
import { ErrorSummary } from '@/components/shared';

const FIELD_ID = 'id_comment-comment';

type PublishCommentStepProps = {
  comment: string;
  hint: string;
  errorMessage: string;
  disabled?: boolean;
  onChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  onCancel: () => void;
};

/**
 * The comment step of Django's update wizards (`FeedCommentForm` / `FaresFeedCommentForm`
 * rendered by crispy in `publish/feed_form.html`).
 */
export function PublishCommentStep({
  comment,
  hint,
  errorMessage,
  disabled = false,
  onChange,
  onSubmit,
  onCancel,
}: Readonly<PublishCommentStepProps>) {
  return (
    <form onSubmit={onSubmit} noValidate>
      <ErrorSummary errors={errorMessage ? [{ text: errorMessage, href: `#${FIELD_ID}` }] : []} />
      <h1 className="govuk-heading-xl">Provide a comment on what has been updated</h1>
      <div className={`govuk-form-group${errorMessage ? ' govuk-form-group--error' : ''}`}>
        <label className="govuk-label" htmlFor={FIELD_ID}>
          Comment on data set updates
        </label>
        <span id={`${FIELD_ID}-hint`} className="govuk-hint">
          {hint}
        </span>
        {errorMessage ? (
          <span id={`1_${FIELD_ID}-error`} className="govuk-error-message">
            {errorMessage}
          </span>
        ) : null}
        <textarea
          className={`govuk-!-width-three-quarters govuk-textarea${errorMessage ? ' govuk-textarea--error' : ''}`}
          id={FIELD_ID}
          name="comment-comment"
          cols={40}
          rows={3}
          placeholder=""
          aria-describedby={`${FIELD_ID}-hint`}
          required
          value={comment}
          onChange={(event) => onChange(event.target.value)}
        />
      </div>
      <div className="button-holder">
        <button type="submit" name="submit" value="submit" className="govuk-button" data-module="govuk-button" disabled={disabled}>
          Continue
        </button>
        <button
          type="button"
          name="cancel"
          value="cancel"
          className="govuk-button govuk-button--secondary"
          data-module="govuk-button"
          onClick={onCancel}
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
