'use client';

import { FormEvent, useState } from 'react';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AvlUploadFields, PublishStepper } from '@/components/publish';
import { Modal } from '@/components/shared';
import { validateAvlCommentStep, validateAvlUploadStep } from '@/lib/validation/avl-publish';

type Step = 'comment' | 'cancel' | 'upload';

function getHeading(step: Step): string {
  if (step === 'comment') {
    return 'Add comment to your feed (optional)';
  }
  return 'Update your published data feed';
}

function AVLUpdatePageContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const listUrl = `/publish/org/${orgId}/dataset/avl`;

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

  const onContinueFromComment = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const validationErrors = validateAvlCommentStep({ comment });
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setSubmitError('');
    setStep('upload');
  };

  const onContinueFromUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const validationErrors = validateAvlUploadStep({ urlLink, username, password });
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setSubmitError('');
    setIsSubmitting(true);

    try {
      const token = globalThis.window ? globalThis.window.localStorage.getItem('bods.auth.access') : null;
      const formData = new FormData();
      formData.set('comment', comment);
      formData.set('url_link', urlLink);
      formData.set('username', username);
      formData.set('password', password);
      formData.set('requestor_ref', requestorRef);

      const response = await fetch(`/api/avl/update?orgId=${orgId}&datasetId=${datasetId}`, {
        method: 'POST',
        body: formData,
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      const data = (await response.json().catch(() => ({}))) as { error?: string; redirect?: string };

      if (!response.ok) {
        setSubmitError(data.error || `Submit failed (${response.status}).`);
        setIsSubmitting(false);
        return;
      }

      if (!data.redirect) {
        setSubmitError('Unexpected response from server.');
        setIsSubmitting(false);
        return;
      }

      globalThis.location.href = data.redirect;
    } catch {
      setSubmitError('An error occurred while submitting. Please try again.');
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
    globalThis.location.href = `/publish/org/${orgId}/dataset/avl/${datasetId}/review`;
  };

  const activeStep = step === 'cancel' ? stepBeforeCancel : step;

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
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
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-l">{getHeading(activeStep)}</h1>

            {submitError && (
              <div className="govuk-error-summary" role="alert" aria-labelledby="avl-update-error-title">
                <h2 className="govuk-error-summary__title" id="avl-update-error-title">
                  There is a problem
                </h2>
                <div className="govuk-error-summary__body">
                  <ul className="govuk-list govuk-error-summary__list">
                    <li>{submitError}</li>
                  </ul>
                </div>
              </div>
            )}

            {activeStep === 'comment' && (
              <form method="post" onSubmit={onContinueFromComment} noValidate>
                <div className={`govuk-form-group ${errors.comment ? 'govuk-form-group--error' : ''}`}>
                  <label className="govuk-label" htmlFor="id_comment">
                    Comment on data feed updates
                  </label>
                  <div className="govuk-hint">
                    Please add a comment to describe the data feed update.
                  </div>
                  {errors.comment && <p className="govuk-error-message">{errors.comment}</p>}
                  <textarea
                    className="govuk-textarea govuk-!-width-three-quarters"
                    id="id_comment"
                    rows={3}
                    value={comment}
                    onChange={(event) => setComment(event.target.value)}
                  />
                </div>

                <div className="govuk-button-group">
                  <button type="submit" className="govuk-button">
                    Continue
                  </button>
                  <button type="button" className="govuk-button govuk-button--secondary" onClick={() => onCancelClick('comment')}>
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
                  ipAllowListHint={process.env.NEXT_PUBLIC_AVL_IP_ALLOW_LIST || ''}
                />

                <div className="govuk-button-group govuk-!-margin-top-5">
                  <button type="submit" className="govuk-button" disabled={isSubmitting}>
                    {isSubmitting ? 'Submitting...' : 'Continue'}
                  </button>
                  <button type="button" className="govuk-button govuk-button--secondary" onClick={() => onCancelClick('upload')}>
                    Cancel
                  </button>
                </div>
              </form>
            )}

            <hr className="govuk-section-break govuk-section-break--xl govuk-section-break" />
          </div>
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
