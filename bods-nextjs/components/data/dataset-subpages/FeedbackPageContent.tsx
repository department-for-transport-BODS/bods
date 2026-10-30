'use client';

/**
 * Contact the dataset owner (feedback form) and its success page (data host)
 *
 * Source: transit_odp/browse/templates/browse/timetables/user_feedback.html,
 *         user_feedback_success.html (also used by AVL and fares)
 * Form: transit_odp/browse/forms.py - ConsumerFeedbackForm
 * View: transit_odp/browse/views/timetable_views.py - UserFeedbackView (+ AVL, fares)
 * API: transit_odp/browse/views/api.py - dataset_feedback_api,
 *      get_dataset_feedback_success_api
 */

import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useState, type FormEvent } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ErrorSummary } from '@/components/shared';
import { useFormSubmit } from '@/hooks/useFormSubmit';
import { ApiError, api } from '@/lib/api-client';
import { errorSummaryItems } from '@/lib/form-errors';
import { FeedPageShell } from './FeedPageShell';
import { datasetDetailHref, datasetSubpageApiPath, type DatasetSubpageKind } from './kinds';
import type { DatasetFeedback } from './types';
import { useSubpageResource } from './useSubpageResource';

const LOAD_ERROR = 'Unable to load this page. Please refresh and try again.';
const FEEDBACK_ANCHORS = { feedback: '#id_feedback' };

function withQuery(path: string, query: string): string {
  return query ? `${path}?${query}` : path;
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <p className="govuk-body">
      <span className="govuk-body-l govuk-!-font-weight-bold">{label}</span>
      <span className="govuk-body-l">{value}</span>
    </p>
  );
}

function FeedbackForm({ kind, feedback, query }: { kind: DatasetSubpageKind; feedback: DatasetFeedback; query: string }) {
  const router = useRouter();
  const datasetId = String(feedback.datasetId);
  const [text, setText] = useState('');
  const [anonymous, setAnonymous] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const { isSubmitting, submitError, handleSubmit } = useFormSubmit();

  const summary = errorSummaryItems(fieldErrors, FEEDBACK_ANCHORS);
  const hasErrors = summary.length > 0;

  useEffect(() => {
    document.title = `${hasErrors ? 'Error: ' : ''}Provide feedback`;
  }, [hasErrors]);

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setFieldErrors({});
    void handleSubmit(async () => {
      try {
        const { redirectPath } = await api.post<{ redirectPath: string }>(
          withQuery(datasetSubpageApiPath(kind, datasetId, 'feedback'), query),
          { feedback: text, anonymous },
        );
        router.push(redirectPath);
      } catch (error) {
        if (error instanceof ApiError && error.hasFieldErrors) {
          setFieldErrors(error.firstFieldErrors());
          return;
        }
        throw error;
      }
    });
  };

  // Django decides on the dataset's own type, not on the URL it was reached by.
  const noun = feedback.datasetType === 'AVL' ? 'data feed' : 'data set';
  const feedbackError = fieldErrors.feedback;

  return (
    <FeedPageShell backHref={feedback.backPath}>
      <div className="govuk-grid-row">
        <div className="govuk-grid-column-two-thirds">
          <h1 className="govuk-heading-l">Contact the {noun} owner</h1>
          <p className="govuk-body">
            An email generated from this form will be sent to the {noun} owner directly. They will be your point of
            contact for any potential resolution to your query.
          </p>
          <br />
          <DetailRow label="Name " value={feedback.name} />
          <DetailRow label={feedback.datasetType === 'AVL' ? 'Data feed ID ' : 'Data set ID '} value={String(feedback.datasetId)} />
          {feedback.service ? <DetailRow label="Service " value={`${feedback.lineName} - ${feedback.service}`} /> : null}
          {feedback.stopName ? <DetailRow label="Timing Point " value={`${feedback.stopName} - ${feedback.atcoCode}`} /> : null}
          {feedback.journeyStartTime ? (
            <>
              <DetailRow label="Journey Start Time " value={feedback.journeyStartTime} />
              <DetailRow label="Direction " value={feedback.direction ?? ''} />
            </>
          ) : null}
          <form onSubmit={onSubmit} noValidate>
            <ErrorSummary
              errors={hasErrors ? summary : submitError ? [submitError] : []}
              tabIndex={-1}
              dataModule="govuk-error-summary"
            />
            <div className={`govuk-form-group${feedbackError ? ' govuk-form-group--error' : ''}`}>
              <label className="govuk-label" htmlFor="id_feedback">
                What best describes the issue you are experiencing?*
              </label>
              {feedbackError ? (
                <span id="1_id_feedback-error" className="govuk-error-message">
                  {feedbackError}
                </span>
              ) : null}
              <textarea
                name="feedback"
                cols={40}
                rows={3}
                className={`govuk-textarea${feedbackError ? ' govuk-textarea--error' : ''}`}
                required
                id="id_feedback"
                value={text}
                onChange={(event) => setText(event.target.value)}
              />
            </div>
            <div className="govuk-form-group">
              <div className="govuk-checkboxes">
                <div className="govuk-checkboxes__item">
                  <input
                    type="checkbox"
                    name="anonymous"
                    className="govuk-checkboxes__input"
                    id="id_anonymous"
                    checked={anonymous}
                    onChange={(event) => setAnonymous(event.target.checked)}
                  />
                  <label htmlFor="id_anonymous" className="govuk-label govuk-checkboxes__label">
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
    </FeedPageShell>
  );
}

function Feedback({ kind }: { kind: DatasetSubpageKind }) {
  const datasetId = useParams().id as string;
  const query = useSearchParams().toString();
  const { data, error } = useSubpageResource<DatasetFeedback>(
    withQuery(datasetSubpageApiPath(kind, datasetId, 'feedback'), query),
    LOAD_ERROR,
  );

  if (!data) return <FeedPageShell backHref={datasetDetailHref(kind, datasetId)} error={error} />;

  return <FeedbackForm kind={kind} feedback={data} query={query} />;
}

export function FeedbackPageContent({ kind }: { kind: DatasetSubpageKind }) {
  return (
    <ProtectedRoute>
      <Suspense fallback={null}>
        <Feedback kind={kind} />
      </Suspense>
    </ProtectedRoute>
  );
}

function FeedbackSuccess({ kind }: { kind: DatasetSubpageKind }) {
  const datasetId = useParams().id as string;
  const query = useSearchParams().toString();
  const { data, error } = useSubpageResource<{ backPath: string }>(
    withQuery(datasetSubpageApiPath(kind, datasetId, 'feedback/success'), query),
    LOAD_ERROR,
  );

  useEffect(() => {
    document.title = 'Feedback sent';
  }, []);

  if (!data) return <FeedPageShell error={error} />;

  return (
    <FeedPageShell backHref={data.backPath}>
      <div className="govuk-grid-row">
        <div className="govuk-grid-column-two-thirds">
          <h1 className="govuk-heading-l app-!-mb-4">Your feedback has been submitted</h1>
          <div className="btn-group-justified">
            <a role="button" className="govuk-button app-!-mr-sm-4" href={data.backPath}>
              Go back to data set
            </a>
          </div>
        </div>
      </div>
    </FeedPageShell>
  );
}

export function FeedbackSuccessPageContent({ kind }: { kind: DatasetSubpageKind }) {
  return (
    <ProtectedRoute>
      <Suspense fallback={null}>
        <FeedbackSuccess kind={kind} />
      </Suspense>
    </ProtectedRoute>
  );
}
