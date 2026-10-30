'use client';

/**
 * Contact an operator (data host, `/operators/<pk>/contact/`)
 *
 * Source: transit_odp/browse/templates/browse/operators/contact_operator.html
 * View: transit_odp/browse/views/contact_operator.py - ContactOperatorView
 * API: transit_odp/browse/views/operators_api.py - operator_contact_api
 */

import Link from 'next/link';
import { notFound, useRouter } from 'next/navigation';
import { useEffect, useState, type FormEvent } from 'react';
import { ErrorDisplay } from '@/components/shared/ErrorDisplay';
import { ErrorSummary } from '@/components/shared/ErrorSummary';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { ApiError, api } from '@/lib/api-client';
import { errorSummaryItems } from '@/lib/form-errors';
import {
  operatorContactApiPath,
  operatorContactSuccessUrl,
  operatorDetailUrl,
  type OperatorContact,
} from '@/lib/operators';

interface ContactOperatorContentProps {
  operatorId: string;
}

export function ContactOperatorContent({ operatorId }: ContactOperatorContentProps) {
  const router = useRouter();
  const [operator, setOperator] = useState<OperatorContact | null>(null);
  const [loadError, setLoadError] = useState('');
  const [missing, setMissing] = useState(false);
  const [feedback, setFeedback] = useState('');
  const [anonymous, setAnonymous] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const hasErrors = Object.keys(fieldErrors).length > 0 || Boolean(formError);

  useEffect(() => {
    document.title = hasErrors ? 'Error: Provide feedback' : 'Provide feedback';
  }, [hasErrors]);

  useEffect(() => {
    let cancelled = false;
    api
      .get<OperatorContact>(operatorContactApiPath(operatorId))
      .then((response) => {
        if (!cancelled) setOperator(response);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) {
          setMissing(true);
          return;
        }
        setLoadError('Failed to load operator');
      });
    return () => {
      cancelled = true;
    };
  }, [operatorId]);

  if (missing) notFound();

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsSubmitting(true);
    setFieldErrors({});
    setFormError('');
    try {
      await api.post(operatorContactApiPath(operatorId), { feedback, anonymous });
      router.push(operatorContactSuccessUrl(operatorId));
    } catch (err: unknown) {
      if (err instanceof ApiError && err.hasFieldErrors) {
        setFieldErrors(err.firstFieldErrors());
      } else {
        setFormError('There was a problem sending your feedback. Please try again.');
      }
      setIsSubmitting(false);
    }
  };

  const feedbackError = fieldErrors.feedback;
  const summaryItems = [
    ...errorSummaryItems(fieldErrors, { feedback: '#id_feedback' }),
    ...(formError ? [formError] : []),
  ];

  return (
    <div className="govuk-width-container">
      <Link className="govuk-back-link" href={operatorDetailUrl(operatorId)}>
        Back
      </Link>
      <div className="govuk-main-wrapper">
        {loadError && <ErrorDisplay message={loadError} />}
        {!operator && !loadError && <LoadingSpinner message="Loading" />}
        {operator && (
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-two-thirds">
              <h1 className="govuk-heading-l">Contact {operator.name}</h1>
              <p className="govuk-body">
                An email generated from this form will be sent to the data set/data feed owner directly. They will be
                your point of contact for any potential resolution to your query.
              </p>
              <br />
              <ErrorSummary errors={summaryItems} />
              <form method="post" noValidate onSubmit={handleSubmit}>
                <div className={`govuk-form-group${feedbackError ? ' govuk-form-group--error' : ''}`}>
                  <label className="govuk-label" htmlFor="id_feedback">
                    What best describes the issue you are experiencing?*
                  </label>
                  {feedbackError && (
                    <p id="feedback-error" className="govuk-error-message">
                      <span className="govuk-visually-hidden">Error:</span> {feedbackError}
                    </p>
                  )}
                  <textarea
                    className={`govuk-textarea${feedbackError ? ' govuk-textarea--error' : ''}`}
                    id="id_feedback"
                    name="feedback"
                    rows={3}
                    value={feedback}
                    onChange={(event) => setFeedback(event.target.value)}
                    aria-describedby={feedbackError ? 'feedback-error' : undefined}
                  />
                </div>
                <div className="govuk-form-group">
                  <div className="govuk-checkboxes" data-module="govuk-checkboxes">
                    <div className="govuk-checkboxes__item">
                      <input
                        className="govuk-checkboxes__input"
                        id="id_anonymous"
                        name="anonymous"
                        type="checkbox"
                        checked={anonymous}
                        onChange={(event) => setAnonymous(event.target.checked)}
                      />
                      <label className="govuk-label govuk-checkboxes__label" htmlFor="id_anonymous">
                        Send this feedback anonymously
                      </label>
                    </div>
                  </div>
                </div>
                <button type="submit" className="govuk-button" data-module="govuk-button" disabled={isSubmitting}>
                  Send
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
