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
} from '@/lib/validation/timetable-publish';
import { TimetableHelpAside } from '../_components/TimetableHelpAside';


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

  const handleNext = () => {
    if (step === 1 && !validateStep1()) {
      return;
    }
    if (step === 2) {
      void handleSubmit();
      return;
    }
    setErrors({});
    setStep(step + 1);
  };

  const handleSubmit = async () => {
    if (!validateStep2()) {
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

            {submitError && <p className="govuk-error-message">{submitError}</p>}

            <hr className="govuk-section-break govuk-section-break--xl govuk-section-break" />
          </div>

          <TimetableHelpAside />
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

