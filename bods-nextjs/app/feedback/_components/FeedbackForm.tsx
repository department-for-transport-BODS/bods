'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ErrorSummary } from '@/components/shared/ErrorSummary';
import { ApiError, api } from '@/lib/api-client';
import { errorSummaryItems } from '@/lib/form-errors';

const MAX_COMMENT_LENGTH = 1200;

const RATINGS = [
  { value: '1', label: 'Very satisfied' },
  { value: '2', label: 'Satisfied' },
  { value: '3', label: 'Neither satisfied nor dissatisfied' },
  { value: '4', label: 'Dissatisfied' },
  { value: '5', label: 'Very dissatisfied' },
];

type FeedbackFormProps = {
  pageUrl: string;
};

export function FeedbackForm({ pageUrl }: FeedbackFormProps) {
  const router = useRouter();
  const [rating, setRating] = useState('2');
  const [comment, setComment] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const errors = [
    ...errorSummaryItems(fieldErrors, {
      satisfaction_rating: '#satisfaction_rating_1',
      comment: '#comment',
    }),
    ...(submitError ? [submitError] : []),
  ];

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFieldErrors({});
    setSubmitError('');
    setIsSubmitting(true);

    try {
      await api.post('/api/www/feedback/', {
        satisfaction_rating: Number(rating),
        comment,
        page_url: pageUrl,
      });
      router.push('/feedback/thank-you/');
    } catch (error) {
      if (error instanceof ApiError && error.hasFieldErrors) {
        setFieldErrors(error.firstFieldErrors());
      } else {
        setSubmitError(
          error instanceof Error ? error.message : 'Feedback could not be submitted. Try again.',
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <h1 className="govuk-heading-l">Give feedback on Bus Open Data Service</h1>
      <ErrorSummary errors={errors} />

      <form onSubmit={handleSubmit} noValidate>
        <fieldset
          className="govuk-fieldset"
          aria-describedby={fieldErrors.satisfaction_rating ? 'satisfaction-rating-error' : undefined}
        >
          <legend className="govuk-label govuk-!-font-weight-bold">
            How did you find Bus Open Data Service today?
          </legend>
          {fieldErrors.satisfaction_rating && (
            <p className="govuk-error-message" id="satisfaction-rating-error">
              <span className="govuk-visually-hidden">Error:</span>{' '}
              {fieldErrors.satisfaction_rating}
            </p>
          )}
          <div className="govuk-radios">
            {RATINGS.map((option) => (
              <div className="govuk-radios__item" key={option.value}>
                <input
                  className="govuk-radios__input"
                  id={`satisfaction_rating_${option.value}`}
                  name="satisfaction_rating"
                  type="radio"
                  value={option.value}
                  checked={rating === option.value}
                  onChange={(event) => setRating(event.target.value)}
                  required={option.value === '1'}
                />
                <label
                  className="govuk-label govuk-radios__label"
                  htmlFor={`satisfaction_rating_${option.value}`}
                >
                  {option.label}
                </label>
              </div>
            ))}
          </div>
        </fieldset>

        <div className="govuk-form-group govuk-!-margin-top-6">
          <label className="govuk-label govuk-!-font-weight-bold" htmlFor="comment">
            How could we improve this service? (optional)
          </label>
          <div id="comment-hint" className="govuk-hint">
            Do not include any personal or financial information such as your National Insurance or credit card numbers.
          </div>
          {fieldErrors.comment && (
            <p className="govuk-error-message" id="comment-error">
              <span className="govuk-visually-hidden">Error:</span> {fieldErrors.comment}
            </p>
          )}
          <textarea
            className={`govuk-textarea${fieldErrors.comment ? ' govuk-textarea--error' : ''}`}
            id="comment"
            name="comment"
            rows={6}
            maxLength={MAX_COMMENT_LENGTH}
            value={comment}
            aria-describedby={
              ['comment-hint', fieldErrors.comment ? 'comment-error' : null]
                .filter(Boolean)
                .join(' ')
            }
            onChange={(event) => setComment(event.target.value)}
          />
          <div className="govuk-hint">You have {MAX_COMMENT_LENGTH - comment.length} characters remaining</div>
        </div>

        <input type="hidden" name="page_url" value={pageUrl} readOnly />
        <button className="govuk-button" type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Sending feedback...' : 'Send Feedback'}
        </button>
      </form>
    </>
  );
}
