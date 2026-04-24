/**
 * Timetable Publishing Page
 *
 * Multi-step timetable publish flow.
 */

"use client";

import { useState } from "react";
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api-client";
import { useFormSubmit } from "@/hooks/useFormSubmit";
import { PublishStepper, DatasetDescriptionFields, DataProviderRadioGroup, URL_LINK_ITEM_ID, UPLOAD_FILE_ITEM_ID } from '@/components/publish';
import type { StepState } from '@/components/publish';
import {
  validateTimetableStep1,
  validateTimetableStep2,
  validateTimetableStep3,
} from '@/lib/validation/timetable-publish';

function TimetablePublish() {
  const params = useParams();
  const router = useRouter();
  const orgId = params.orgId as string;

  const [dataSetDesc, setDataSetDesc] = useState('');
  const [shortDesc, setShortDesc] = useState('');
  const [step, setStep] = useState(1);
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
        `/api/timetables/create/${orgId}/`,
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

      router.push(`/publish/org/${orgId}/dataset/timetable/success`);
    });
  };

  const stepLabels = ['1. Describe your data set', '2. Provide data', '3. Set licence'];
  const steps = stepLabels.map((label, i) => {
    const stepNum = i + 1;
    let state: StepState = 'next';
    if (stepNum < step) state = 'previous';
    else if (stepNum === step) state = 'selected';
    return { label, state };
  });

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <PublishStepper steps={steps} />

          <hr className="govuk-section-break govuk-section-break--visible" />

          {step === 1 && (
            <div className="govuk-grid-column-two-thirds">
              <h1 className="govuk-heading-xl">Describe your data set</h1>
              <DatasetDescriptionFields
                description={dataSetDesc}
                shortDescription={shortDesc}
                errors={{ description: errors.dataSetDesc, shortDescription: errors.shortDesc }}
                onDescriptionChange={setDataSetDesc}
                onShortDescriptionChange={setShortDesc}
              />
              <button type="button" className="govuk-button" onClick={handleNext}>Continue</button>
            </div>
          )}

          {step === 2 && (
            <div className="govuk-grid-column-two-thirds">
              <h1 className="govuk-heading-xl">Choose how to provide your data set</h1>
              <DataProviderRadioGroup
                selectedMethod={selectedMethod}
                link={link}
                errors={{ method: errors.method, link: errors.link, file: errors.file }}
                onMethodChange={setSelectedMethod}
                onLinkChange={setLink}
                onFileChange={setFile}
              />
              <button type="button" className="govuk-button" onClick={handleNext}>Continue</button>
            </div>
          )}

          {step === 3 && (
            <div className="govuk-grid-column-two-thirds">
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

