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

function TimetablePublish() {
  const params = useParams();
  const router = useRouter();
  const orgId = params.orgId as string;

  const [dataSetDesc, setDataSetDesc] = useState('');
  const [shortDesc, setShortDesc] = useState('');
  const [step, setStep] = useState(1);
  const [selectedMethod, setSelectedMethod] = useState('');
  const [link, setLink] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [consentChecked, setConsentChecked] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const URL_LINK_ITEM_ID = 'url_link-conditional';
  const UPLOAD_FILE_ITEM_ID = 'upload_file-conditional';

  const validateStep1 = () => {
    const newErrors: Record<string, string> = {};
    if (!dataSetDesc.trim()) {
      newErrors.dataSetDesc = 'Enter a description in the data set description box below';
    }
    if (!shortDesc.trim()) {
      newErrors.shortDesc = 'Enter a short description in the data set short description box below';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateStep2 = () => {
    const newErrors: Record<string, string> = {};
    if (!selectedMethod) {
      newErrors.method = 'Select how you want to provide your data set';
    } else if (selectedMethod === 'link' && !link.trim()) {
      newErrors.link = 'Please provide a URL link';
    } else if (selectedMethod === 'file') {
      if (!file) {
        newErrors.file = 'Please provide a file';
      } else {
        const fileName = file.name.toLowerCase();
        if (!fileName.endsWith('.xml') && !fileName.endsWith('.zip')) {
          newErrors.file = 'The selected file must be a TransXChange XML file or a zip file containing only TransXChange files';
        }
      }
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const validateStep3 = () => {
    if (consentChecked) {
      return true;
    }
    setErrors({ consent: 'You must confirm you have reviewed the data quality report before publishing' });
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

    setIsSubmitting(true);
    setErrors({});

    try {
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
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Upload failed. Please try again.';
      setErrors({ submit: message });
    } finally {
      setIsSubmitting(false);
    }
  };

  const checkStep = (stepNumber: number) => {
    if (stepNumber < step) return 'publish-stepper__item publish-stepper__item--previous';
    if (stepNumber === step) return 'publish-stepper__item publish-stepper__item--selected';
    return 'publish-stepper__item publish-stepper__item--next';
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <ol className="publish-stepper govuk-breadcrumbs__list">
            <li className={checkStep(1)}>1. Describe your data set</li>
            <li className={checkStep(2)}>2. Provide data</li>
            <li className={checkStep(3)}>3. Set licence</li>
          </ol>

          <hr className="govuk-section-break govuk-section-break--visible" />

          {step === 1 && (
            <div className="govuk-grid-column-two-thirds">
              <h1 className="govuk-heading-xl">Describe your data set</h1>
              <div className={`govuk-form-group ${errors.dataSetDesc ? 'govuk-form-group--error' : ''}`}>
                <label className="govuk-label" htmlFor="id_description">Data set description</label>
                {errors.dataSetDesc && <p className="govuk-error-message">{errors.dataSetDesc}</p>}
                <textarea className="govuk-textarea" id="id_description" rows={3} maxLength={300} value={dataSetDesc} onChange={(e) => setDataSetDesc(e.target.value)} />
              </div>
              <div className={`govuk-form-group ${errors.shortDesc ? 'govuk-form-group--error' : ''}`}>
                <label className="govuk-label" htmlFor="id_short_description">Dataset short description</label>
                {errors.shortDesc && <p className="govuk-error-message">{errors.shortDesc}</p>}
                <input className="govuk-input" id="id_short_description" type="text" maxLength={30} value={shortDesc} onChange={(e) => setShortDesc(e.target.value)} />
                <span className="govuk-hint">You have {30 - shortDesc.length} characters remaining.</span>
              </div>
              <button type="button" className="govuk-button" onClick={handleNext}>Continue</button>
            </div>
          )}

          {step === 2 && (
            <div className="govuk-grid-column-two-thirds">
              <h1 className="govuk-heading-xl">Choose how to provide your data set</h1>
              {errors.method && <p className="govuk-error-message">{errors.method}</p>}
              <div className="govuk-radios" data-module="govuk-radios">
                <div className="govuk-radios__item">
                  <input className="govuk-radios__input" id="method-link" type="radio" name="method" checked={selectedMethod === 'link'} onChange={() => setSelectedMethod('link')} />
                  <label className="govuk-label govuk-radios__label" htmlFor="method-link">Provide a link to your data set</label>
                </div>
                {selectedMethod === 'link' && (
                  <div className="govuk-form-group">
                    <label className="govuk-label" htmlFor="id_url_link">URL link</label>
                    {errors.link && <p className="govuk-error-message">{errors.link}</p>}
                    <input className="govuk-input" id="id_url_link" type="url" value={link} onChange={(e) => setLink(e.target.value)} />
                  </div>
                )}
                <div className="govuk-radios__item">
                  <input className="govuk-radios__input" id="method-file" type="radio" name="method" checked={selectedMethod === 'file'} onChange={() => setSelectedMethod('file')} />
                  <label className="govuk-label govuk-radios__label" htmlFor="method-file">Upload data set to Bus Open Data Service</label>
                </div>
                {selectedMethod === 'file' && (
                  <div className="govuk-form-group">
                    <label className="govuk-label" htmlFor="id_upload_file">Upload file</label>
                    {errors.file && <p className="govuk-error-message">{errors.file}</p>}
                    <input className="govuk-file-upload" id="id_upload_file" type="file" accept=".xml,.zip" onChange={(e) => setFile(e.target.files?.[0] || null)} />
                  </div>
                )}
              </div>
              <button type="button" className="govuk-button" onClick={handleNext}>Continue</button>
            </div>
          )}

          {step === 3 && (
            <div className="govuk-grid-column-two-thirds">
              <h1 className="govuk-heading-xl">Review and publish</h1>
              {errors.submit && <p className="govuk-error-message">{errors.submit}</p>}
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

