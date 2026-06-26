'use client';

import { FormEvent, useState } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AvlUploadFields, DatasetDescriptionFields, PublishStepper } from '@/components/publish';
import { ErrorSummary, Modal } from '@/components/shared';
import { getCsrfToken } from '@/lib/api-client';
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
  const supportBusOperatorsUrl = `${djangoPublishBaseUrl}/guidance/operator-requirements/`;
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
    setSubmitError('');
    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);

    try {
      const formData = new FormData();
      formData.set('description', description);
      formData.set('short_description', shortDescription);
      formData.set('url_link', urlLink);
      formData.set('username', username);
      formData.set('password', password);
      formData.set('requestor_ref', requestorRef);

      const headers = new Headers();
      const csrfToken = getCsrfToken();
      if (csrfToken) {
        headers.set('X-CSRFToken', csrfToken);
      }

      const response = await fetch(`${config.djangoApiUrl}/api/avl/create/${orgId}/`, {
        method: 'POST',
        body: formData,
        headers,
        credentials: 'include',
      });

      const data = (await response.json().catch(() => ({}))) as { error?: string; redirect?: string };
      const dataWithFieldErrors = data as {
        error?: string;
        redirect?: string;
        fieldErrors?: Record<string, string[] | string>;
      };

      if (!response.ok) {
        const nextErrors: Record<string, string> = {};
        const fieldErrors = dataWithFieldErrors.fieldErrors || {};

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
        } else {
          setSubmitError(data.error || `Submit failed (${response.status}).`);
        }
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
  const uploadValidationSummaryErrors =
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
          <div className="govuk-grid-column-two-thirds indented-text">
            {uploadValidationSummaryErrors.length > 0 && <ErrorSummary errors={uploadValidationSummaryErrors} summaryId="avl-create-error-title" />}

            <h1 className="govuk-heading-l">{getHeading(activeStep)}</h1>
            
            {submitError && (
              <ErrorSummary errors={[submitError]} summaryId="avl-create-submit-error-title" />
            )}

            {activeStep === 'description' && (
              <form method="post" onSubmit={onContinueFromDescription} noValidate>
                <DatasetDescriptionFields
                  description={description}
                  shortDescription={shortDescription}
                  descriptionLabel="Data feed description"
                  shortDescriptionLabel="Data feed short description"
                  showShortDescriptionCounter={false}
                  errors={{ description: errors.description, shortDescription: errors.shortDescription }}
                  descriptionHint="The info will give context to data feed users. Please be descriptive but do not use personally identifiable information. Information you may wish to include: time & date of feed connection, reason for updating feed, OpCo/region/zone of feed, services included in feed."
                  shortDescriptionHint="This info will be displayed on your published data feed dashboard to identify this feed and will not be visible to data feed users. The maximum number of characters (with spaces) is 30 characters."
                  descriptionClassName="govuk-!-width-three-quarters"
                  shortDescriptionClassName="govuk-!-width-three-quarters"
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
                <Link href={supportBusOperatorsUrl} className="govuk-link large-font">
                  View our guidelines here
                </Link>
              </li>
              <li>
                <Link href={contactSupportUrl} className="govuk-link large-font">
                  Contact support desk
                </Link>
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
