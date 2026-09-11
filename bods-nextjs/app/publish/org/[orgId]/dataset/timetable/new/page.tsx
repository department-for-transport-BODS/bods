/**
 * Timetable Publishing Page
 *
 * Multi-step timetable publish flow.
 */

"use client";

import { useState } from "react";
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api-client";
import { useFormSubmit } from "@/hooks/useFormSubmit";
import { PublishStepper, DatasetDescriptionFields, DataProviderRadioGroup, URL_LINK_ITEM_ID, UPLOAD_FILE_ITEM_ID } from '@/components/publish';
import { ErrorSummary } from '@/components/shared';
import type { StepState } from '@/components/publish';
import {
  validateTimetableStep1,
  validateTimetableStep2,
  validateTimetableStep3,
} from '@/lib/validation/timetable-publish';
import { publishAppPath, wwwPath } from '@/config/client';


function TimetablePublish() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;

  const [dataSetDesc, setDataSetDesc] = useState('');
  const [shortDesc, setShortDesc] = useState('');
  const [step, setStep] = useState(searchParams.get('step') === 'provide-data' ? 2 : 1);
  const [selectedMethod, setSelectedMethod] = useState<'link' | 'file' | ''>('');
  const [link, setLink] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [consentChecked, setConsentChecked] = useState(false);
  const { isSubmitting, submitError, handleSubmit: onSubmit, clearError } = useFormSubmit();

  const validateStep1 = () => {
    const newErrors = validateTimetableStep1({ dataSetDesc, shortDesc });
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateStep2 = () => {
    const newErrors = validateTimetableStep2({ selectedMethod, link, file });
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateStep3 = () => {
    const newErrors = validateTimetableStep3(consentChecked);
    if (Object.keys(newErrors).length === 0) {
      return true;
    }
    setErrors(newErrors);
    return false;
  };

  const handleNext = () => {
    if ((step === 1 && !validateStep1()) || (step === 2 && !validateStep2())) {
      return;
    }
    setErrors({});
    setStep(step + 1);
  };

  const handleSubmit = async () => {
    if (!validateStep3()) {
      return;
    }

    setErrors({});
    clearError();

    await onSubmit(async () => {
      const formData = new FormData();
      formData.append('description', dataSetDesc);
      formData.append('short_description', shortDesc);
      formData.append(
        'selected_item',
        selectedMethod === 'link' ? URL_LINK_ITEM_ID : UPLOAD_FILE_ITEM_ID,
      );

      if (selectedMethod === 'link') {
        formData.append('url_link', link);
      } else if (selectedMethod === 'file' && file) {
        formData.append('upload_file', file);
      }

      const response = await api.post<{ redirect?: string }>(
        `/api/publish/timetables/create/${orgId}/`,
        formData,
      );

      if (response.redirect) {
        if (response.redirect.startsWith('/')) {
          router.push(response.redirect);
        } else {
          globalThis.location.href = response.redirect;
        }
        return;
      }

      router.push(`/publish/org/${orgId}/dataset/timetable/new/success`);
    });
  };

  const stepLabels = ['1. Describe data', '2. Provide data', '3. Review and publish'];
  const steps = stepLabels.map((label, i) => {
    const stepNum = i + 1;
    let state: StepState = 'next';
    if (stepNum < step) state = 'previous';
    else if (stepNum === step) state = 'selected';
    return { label, state };
  });

  const supportBusOperatorsUrl = publishAppPath('/guidance/operator-requirements');
  const contactSupportUrl = wwwPath('/contact');
  const uploadValidationSummaryErrors = step === 2
    ? [
        errors.method ? { text: errors.method, href: '#method-link' } : null,
        errors.link ? { text: errors.link, href: '#id_url_link' } : null,
        errors.file ? { text: errors.file, href: '#id_upload_file' } : null,
      ].filter((error): error is { text: string; href: string } => error !== null)
    : [];
  const descriptionValidationSummaryErrors = step === 1
    ? [
        errors.dataSetDesc ? { text: errors.dataSetDesc, href: '#id_description' } : null,
        errors.shortDesc ? { text: errors.shortDesc, href: '#id_short_description' } : null,
      ].filter((error): error is { text: string; href: string } => error !== null)
    : [];

  return (
    <div className="govuk-width-container">
      <div className="govuk-breadcrumbs">
        <PublishStepper steps={steps} />
      </div>

      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds indented-text">
            {step === 1 && (
              <div>
                <h1 className="govuk-heading-xl">Describe your data set</h1>
                <ErrorSummary errors={descriptionValidationSummaryErrors} summaryId="timetable-description-error-title" />
                <DatasetDescriptionFields
                  description={dataSetDesc}
                  shortDescription={shortDesc}
                  shortDescriptionLabel="Data set short description"
                  descriptionHint={
                    <>This information will give context to data consumers. Please be descriptive, but do not use personally identifiable information.</>
                  }
                  shortDescriptionHint={
                    <>This info will be displayed on your published data set dashboard to identify this data set and will not be visible to data set users. The maximum number of characters (with spaces) is 30 characters.</>
                  }
                  descriptionClassName="govuk-!-width-three-quarters"
                  shortDescriptionClassName="govuk-!-width-three-quarters"
                  errors={{ description: errors.dataSetDesc, shortDescription: errors.shortDesc }}
                  onDescriptionChange={setDataSetDesc}
                  onShortDescriptionChange={setShortDesc}
                />
                <div className="govuk-button-group">
                  <button type="button" className="govuk-button" onClick={handleNext}>Continue</button>
                  <button type="button" className="govuk-button govuk-button--secondary" onClick={() => router.push(`/publish/org/${orgId}/dataset/timetable/new/cancel`)}>Cancel</button>
                </div>
              </div>
            )}

            {step === 2 && (
              <div>
                <h1 className="govuk-heading-xl">Choose how to provide your data set</h1>
                <ErrorSummary errors={uploadValidationSummaryErrors} summaryId="timetable-upload-error-title" />
                <DataProviderRadioGroup
                  selectedMethod={selectedMethod}
                  link={link}
                  urlHint="Please provide data set URI that contains either TransXChange (see description in guidance) or zip consisting only of TransXChange files"
                  fileHint="Please provide data set file that contains either TransXChange (see description in guidance) or zip consisting only of TransXChange files"
                  fileSelected={file !== null}
                  errors={{ method: errors.method, link: errors.link, file: errors.file }}
                  onMethodChange={setSelectedMethod}
                  onLinkChange={setLink}
                  onFileChange={setFile}
                />
                <div className="govuk-button-group govuk-!-margin-top-5">
                  <button type="button" className="govuk-button" onClick={handleNext}>Continue</button>
                  <button type="button" className="govuk-button govuk-button--secondary" onClick={() => router.push(`/publish/org/${orgId}/dataset/timetable/new/cancel?step=provide-data`)}>Cancel</button>
                </div>
              </div>
            )}

            {step === 3 && (
              <div>
                <h1 className="govuk-heading-xl">Review and publish</h1>
                {submitError && <p className="govuk-error-message">{submitError}</p>}
                <dl className="govuk-summary-list">
                  <div className="govuk-summary-list__row"><dt className="govuk-summary-list__key">Data set description</dt><dd className="govuk-summary-list__value">{dataSetDesc}</dd></div>
                  <div className="govuk-summary-list__row"><dt className="govuk-summary-list__key">Short description</dt><dd className="govuk-summary-list__value">{shortDesc}</dd></div>
                  <div className="govuk-summary-list__row"><dt className="govuk-summary-list__key">Data provided via</dt><dd className="govuk-summary-list__value">{selectedMethod === 'link' ? link : file?.name}</dd></div>
                </dl>
                <div className="govuk-form-group">
                  <div className="govuk-checkboxes__item">
                    <input className="govuk-checkboxes__input" id="id_consent" type="checkbox" checked={consentChecked} onChange={(e) => setConsentChecked(e.target.checked)} />
                    <label className="govuk-label govuk-checkboxes__label" htmlFor="id_consent">I have reviewed the data quality report and wish to publish my data</label>
                  </div>
                  {errors.consent && <p className="govuk-error-message">{errors.consent}</p>}
                </div>
                <button type="button" className="govuk-button" disabled={isSubmitting} onClick={handleSubmit}>{isSubmitting ? 'Publishing...' : 'Publish'}</button>
              </div>
            )}

            <hr className="govuk-section-break govuk-section-break--xl govuk-section-break" />
          </div>

          <div className="govuk-grid-column-one-third">
            <h2 className="govuk-heading-m">Need help with operator data requirements?</h2>
            <ul className="govuk-list app-list--nav govuk-!-font-size-19">
              <li>
                <a className="govuk-link" target="_blank" rel="noopener noreferrer" href={`${supportBusOperatorsUrl}?section=dataquality`}>
                  View the Txc 2.4 schema and profile requirement
                </a>
              </li>
              <li>
                <a className="govuk-link" target="_blank" rel="noopener noreferrer" href={supportBusOperatorsUrl}>
                  View our guidelines here
                </a>
              </li>
              <li>
                <a className="govuk-link" target="_blank" rel="noopener noreferrer" href={contactSupportUrl}>
                  Contact support desk
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function TimetablePublishPage() {
  return (
    <ProtectedRoute>
      <TimetablePublish />
    </ProtectedRoute>
  );
}

