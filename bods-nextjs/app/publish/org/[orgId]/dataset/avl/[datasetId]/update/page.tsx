'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { config } from '@/config';
import { AvlUploadFields, PublishStepper } from '@/components/publish';
import { ErrorSummary, Modal } from '@/components/shared';
import { getCsrfToken } from '@/lib/api-client';
import { validateAvlCommentStep, validateAvlUploadStep } from '@/lib/validation/avl-publish';
import { AvlReviewHelpAside } from '../../_components/AvlReviewAuxiliaryPanels';

type Step = 'comment' | 'cancel' | 'upload';

type AvlUpdateContext = {
  urlLink?: string;
  requestorRef?: string;
  comment?: string;
};

function getHeading(step: Step): string {
  if (step === 'comment') {
    return 'Provide a comment on what has been updated';
  }
  return 'Update your published data feed';
}

function AVLUpdatePageContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const djangoApiBaseUrl = config.djangoApiBaseUrl;
  const djangoPublishBaseUrl = djangoApiBaseUrl.replace('://localhost', '://publish.localhost');
  const supportBusOperatorsUrl = `${djangoPublishBaseUrl}/guidance/operator-requirements/`;
  const contactSupportUrl = `${djangoApiBaseUrl}/contact/`;
  const reviewUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}/update/review`;

  const [step, setStep] = useState<Step>('comment');
  const [stepBeforeCancel, setStepBeforeCancel] = useState<'comment' | 'upload'>('comment');
  const [comment, setComment] = useState('');
  const [urlLink, setUrlLink] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [requestorRef, setRequestorRef] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const moveToTop = () => {
    if (typeof document !== 'undefined') {
      document.getElementById('avl-update-page-top')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  useEffect(() => {
    let cancelled = false;

    const loadExistingDraft = async () => {
      try {
        const response = await fetch(`${config.djangoApiUrl}/api/avl/review-status/${orgId}/${datasetId}/`, {
          credentials: 'include',
        });
        if (!response.ok || cancelled) {
          return;
        }

        const data = (await response.json()) as AvlUpdateContext;
        if (!cancelled) {
          setComment('');
          setUrlLink(data.urlLink || '');
          setRequestorRef(data.requestorRef || '');
        }
      } catch {
        // The update form remains usable even if draft context cannot be preloaded.
      }
    };

    loadExistingDraft();

    return () => {
      cancelled = true;
    };
  }, [datasetId, orgId]);

  const onContinueFromComment = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const validationErrors = validateAvlCommentStep({ comment });
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      moveToTop();
      return;
    }

    setSubmitError('');
    setStep('upload');
  };

  const onContinueFromUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const validationErrors = validateAvlUploadStep({ urlLink, username, password });
    setErrors(validationErrors);
    setSubmitError('');
    if (Object.keys(validationErrors).length > 0) {
      moveToTop();
      return;
    }

    setIsSubmitting(true);

    try {
      const formData = new FormData();
      formData.set('comment', comment);
      formData.set('url_link', urlLink);
      formData.set('username', username);
      formData.set('password', password);
      formData.set('requestor_ref', requestorRef);

      const headers = new Headers();
      const csrfToken = getCsrfToken();
      if (csrfToken) {
        headers.set('X-CSRFToken', csrfToken);
      }

      const response = await fetch(`/api/avl/update?orgId=${orgId}&datasetId=${datasetId}`, {
        method: 'POST',
        body: formData,
        headers,
        credentials: 'include',
      });

      const data = (await response.json().catch(() => ({}))) as {
        error?: string;
        redirect?: string;
        fieldErrors?: Record<string, string[] | string>;
        field_errors?: Record<string, string[] | string>;
      };

      if (!response.ok) {
        const nextErrors: Record<string, string> = {};
        const fieldErrors = data.fieldErrors || data.field_errors || {};

        const commentError = fieldErrors.comment;
        if (commentError) {
          nextErrors.comment = Array.isArray(commentError) ? commentError[0] : commentError;
        }

        const urlLinkError = fieldErrors.url_link;
        if (urlLinkError) {
          nextErrors.urlLink = Array.isArray(urlLinkError) ? urlLinkError[0] : urlLinkError;
        }

        const usernameError = fieldErrors.username;
        if (usernameError) {
          nextErrors.username = Array.isArray(usernameError) ? usernameError[0] : usernameError;
        }

        const passwordError = fieldErrors.password;
        if (passwordError) {
          nextErrors.password = Array.isArray(passwordError) ? passwordError[0] : passwordError;
        }

        const requestorRefError = fieldErrors.requestor_ref;
        if (requestorRefError) {
          nextErrors.requestorRef = Array.isArray(requestorRefError) ? requestorRefError[0] : requestorRefError;
        }

        if (Object.keys(nextErrors).length > 0) {
          setErrors(nextErrors);
          setSubmitError('');
          moveToTop();
        } else {
          setSubmitError(data.error || `Submit failed (${response.status}).`);
          moveToTop();
        }

        setIsSubmitting(false);
        return;
      }

      globalThis.location.href = data.redirect || reviewUrl;
    } catch {
      setSubmitError('An error occurred while submitting. Please try again.');
      moveToTop();
      setIsSubmitting(false);
    }
  };

  const onCancelClick = (from: 'comment' | 'upload') => {
    setStepBeforeCancel(from);
    setStep('cancel');
  };

  const onCancelBack = () => {
    setStep(stepBeforeCancel);
  };

  const onCancelConfirm = () => {
    globalThis.location.href = reviewUrl;
  };

  const activeStep = step === 'cancel' ? stepBeforeCancel : step;

  const commentSummaryErrors =
    activeStep === 'comment'
      ? [errors.comment ? { text: errors.comment, href: '#id_comment' } : null].filter(
          (error): error is { text: string; href: string } => error !== null,
        )
      : [];

  const uploadSummaryErrors =
    activeStep === 'upload'
      ? [
          errors.urlLink ? { text: errors.urlLink, href: '#id_url_link' } : null,
          errors.username ? { text: errors.username, href: '#id_username' } : null,
          errors.password ? { text: errors.password, href: '#id_password' } : null,
          errors.requestorRef ? { text: errors.requestorRef, href: '#id_requestor_ref' } : null,
        ].filter((error): error is { text: string; href: string } => error !== null)
      : [];

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div id="avl-update-page-top" />
        <div className="govuk-breadcrumbs">
          <PublishStepper
            steps={[
              { label: '1. Add update comment', state: activeStep === 'comment' ? 'selected' : 'previous' },
              { label: '2. Provide your data', state: activeStep === 'upload' ? 'selected' : 'next' },
              { label: '3. Review and publish', state: 'next' },
            ]}
          />
        </div>

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds indented-text">
            {commentSummaryErrors.length > 0 && (
              <ErrorSummary errors={commentSummaryErrors} summaryId="avl-update-comment-error-title" />
            )}
            {uploadSummaryErrors.length > 0 && (
              <ErrorSummary errors={uploadSummaryErrors} summaryId="avl-update-upload-error-title" />
            )}

            <h1 className="govuk-heading-l">{getHeading(activeStep)}</h1>

            {submitError && (
              <ErrorSummary errors={[submitError]} summaryId="avl-update-submit-error-title" />
            )}

            {activeStep === 'comment' && (
              <form method="post" onSubmit={onContinueFromComment} noValidate>
                <div className={`govuk-form-group ${errors.comment ? 'govuk-form-group--error' : ''}`}>
                  <label className="govuk-label" htmlFor="id_comment">
                    Comment on data feed updates
                  </label>
                  <div className="govuk-hint">
                    Please add a comment to describe the data feed. Providers may want to include:
                    time and date of feed connection, reason for updating feed, OpCo/Region/Zone of feed,
                    internal references, or services included in the feed.
                  </div>
                  {errors.comment && <p className="govuk-error-message">{errors.comment}</p>}
                  <textarea
                    id="id_comment"
                    className="govuk-textarea govuk-!-width-three-quarters"
                    rows={4}
                    value={comment}
                    onChange={(event) => {
                      setComment(event.target.value);
                      setErrors({});
                    }}
                  />
                </div>

                <div className="govuk-button-group">
                  <button type="submit" className="govuk-button">
                    Continue
                  </button>
                  <button
                    type="button"
                    className="govuk-button govuk-button--secondary"
                    onClick={() => onCancelClick('comment')}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}

            <Modal
              open={step === 'cancel'}
              title="Would you like to cancel updating this data feed?"
              description="Any changes you have made so far will not be saved."
              onClose={onCancelBack}
            >
              <div className="govuk-button-group">
                <button type="button" className="govuk-button" onClick={onCancelConfirm}>
                  Confirm
                </button>
                <button type="button" className="govuk-button govuk-button--secondary" onClick={onCancelBack}>
                  Cancel
                </button>
              </div>
            </Modal>

            {activeStep === 'upload' && (
              <form method="post" onSubmit={onContinueFromUpload} noValidate>
                <AvlUploadFields
                  urlLink={urlLink}
                  username={username}
                  password={password}
                  requestorRef={requestorRef}
                  guidanceUrl={supportBusOperatorsUrl}
                  errors={{
                    urlLink: errors.urlLink,
                    username: errors.username,
                    password: errors.password,
                    requestorRef: errors.requestorRef,
                  }}
                  onUrlLinkChange={setUrlLink}
                  onUsernameChange={setUsername}
                  onPasswordChange={setPassword}
                  onRequestorRefChange={setRequestorRef}
                  ipAllowListHint={config.avlIpAllowList}
                />

                <div className="govuk-button-group govuk-!-margin-top-5">
                  <button type="submit" className="govuk-button" disabled={isSubmitting}>
                    {isSubmitting ? 'Submitting...' : 'Continue'}
                  </button>
                  <button
                    type="button"
                    className="govuk-button govuk-button--secondary"
                    onClick={() => onCancelClick('upload')}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}

            <hr className="govuk-section-break govuk-section-break--xl govuk-section-break" />
          </div>

          <AvlReviewHelpAside
            supportBusOperatorsUrl={supportBusOperatorsUrl}
            contactSupportUrl={contactSupportUrl}
            linkClassName="govuk-link large-font"
            openInNewTab
          />
        </div>
      </div>
    </div>
  );
}

export default function AVLUpdatePage() {
  return (
    <ProtectedRoute>
      <AVLUpdatePageContent />
    </ProtectedRoute>
  );
}
