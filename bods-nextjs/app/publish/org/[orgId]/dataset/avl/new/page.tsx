'use client';

import { FormEvent, useState } from 'react';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AvlUploadFields, DatasetDescriptionFields, PublishStepper } from '@/components/publish';
import { LinkWithArrow, Modal } from '@/components/shared';
import { validateAvlDescriptionStep, validateAvlUploadStep } from '@/lib/validation/avl-publish';
import { config } from '@/config';

type Step = 'description' | 'cancel' | 'upload';

function getHeading(step: Step): string {
  if (step === 'description') {
    return 'Describe your data feed';
  }
  return 'Provide your data using the link below';
}

function AVLCreatePageContent() {
  const params = useParams();
  const orgId = params.orgId as string;

  const djangoApiBaseUrl = config.djangoApiBaseUrl;
  const djangoPublishBaseUrl = djangoApiBaseUrl.replace('://localhost', '://publish.localhost');
  const supportBusOperatorsUrl = `${djangoPublishBaseUrl}/guidance/operator-requirements/?section=buslocation`;
  const contactSupportUrl = `${djangoApiBaseUrl}/contact/`;
  const listUrl = `/publish/org/${orgId}/dataset/avl`;

  const [step, setStep] = useState<Step>('description');
  const [stepBeforeCancel, setStepBeforeCancel] = useState<'description' | 'upload'>('description');
  const [description, setDescription] = useState('');
  const [shortDescription, setShortDescription] = useState('');
  const [urlLink, setUrlLink] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [requestorRef, setRequestorRef] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const onContinueFromDescription = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const validationErrors = validateAvlDescriptionStep({ description, shortDescription });
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
      formData.set('description', description);
      formData.set('short_description', shortDescription);
      formData.set('url_link', urlLink);
      formData.set('username', username);
      formData.set('password', password);
      formData.set('requestor_ref', requestorRef);

      const response = await fetch(`/api/avl/create?orgId=${orgId}`, {
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

  const onCancelClick = (from: 'description' | 'upload') => {
    setStepBeforeCancel(from);
    setStep('cancel');
  };

  const onCancelBack = () => {
    setStep(stepBeforeCancel);
  };

  const onCancelConfirm = () => {
    globalThis.location.href = listUrl;
  };

  const activeStep = step === 'cancel' ? stepBeforeCancel : step;

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-breadcrumbs">
          <PublishStepper
            steps={[
              { label: '1. Describe your data feed', state: activeStep === 'description' ? 'selected' : 'previous' },
              { label: '2. Provide your data', state: activeStep === 'upload' ? 'selected' : 'next' },
              { label: '3. Review and publish', state: 'next' },
            ]}
          />
        </div>

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-l">{getHeading(activeStep)}</h1>

            {submitError && (
              <div className="govuk-error-summary" role="alert" aria-labelledby="avl-create-error-title">
                <h2 className="govuk-error-summary__title" id="avl-create-error-title">
                  There is a problem
                </h2>
                <div className="govuk-error-summary__body">
                  <ul className="govuk-list govuk-error-summary__list">
                    <li>{submitError}</li>
                  </ul>
                </div>
              </div>
            )}

            {activeStep === 'description' && (
              <form method="post" onSubmit={onContinueFromDescription} noValidate>
                <DatasetDescriptionFields
                  description={description}
                  shortDescription={shortDescription}
                  errors={{ description: errors.description, shortDescription: errors.shortDescription }}
                  descriptionHint="The info will give context to data feed users."
                  shortDescriptionHint="Maximum number of characters is 30."
                  onDescriptionChange={setDescription}
                  onShortDescriptionChange={setShortDescription}
                />

                <div className="govuk-button-group">
                  <button type="submit" className="govuk-button">
                    Continue
                  </button>
                  <button type="button" className="govuk-button govuk-button--secondary" onClick={() => onCancelClick('description')}>
                    Cancel
                  </button>
                </div>
              </form>
            )}

            <Modal
              open={step === 'cancel'}
              title="Would you like to cancel publishing this data feed?"
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

          <div className="govuk-grid-column-one-third">
            <h2 className="govuk-heading-m">Need help with operator data requirements?</h2>
            <ul className="govuk-list app-list--nav govuk-!-font-size-19">
              <li>
                <LinkWithArrow href={supportBusOperatorsUrl} className="govuk-link large-font">
                  View our guidelines here
                </LinkWithArrow>
              </li>
              <li>
                <LinkWithArrow href={contactSupportUrl} className="govuk-link large-font">
                  Contact support desk
                </LinkWithArrow>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AVLCreatePage() {
  return (
    <ProtectedRoute>
      <AVLCreatePageContent />
    </ProtectedRoute>
  );
}
