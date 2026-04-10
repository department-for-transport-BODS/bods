"use client"; 

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api-client";
import { ApiError } from "@/lib/api-client";
import {
    DATA_QUALITY_LABEL,
    DATA_QUALITY_WITH_VIOLATIONS_LABEL,
    ERROR_CODE_LOOKUP,
    ERROR_TYPE_PII,
    NEXT_STEPS_PII,
    ERROR_TYPE_SERVICE_CHECK,
    NEXT_STEPS_SERVICE_CHECK,
} from "@/lib/constants/timetables";

export default function CreateForm() {
    const params = useParams();
    const router = useRouter();
    const orgId = params.orgId as string;
    const [dataSetDesc, setDataSetDesc] = useState("");
    const [shortDesc, setShortDesc] = useState("");
    const [step, setStep] = useState(1);
    const [selected, setSelected] = useState('');
    const [link, setLink] = useState('')
    const [file, setFile] = useState<File | null>(null)
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [consentChecked, setConsentChecked] = useState(false);
    const [hasViolations, setHasViolations] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const validateStep1 = () => {
        const newErrors: Record<string, string> = {};
        if (!dataSetDesc.trim()) {
            newErrors.dataSetDesc = "Enter a description in the data set description box below";
        }
        if (!shortDesc.trim()) {
            newErrors.shortDesc = "Enter a short description in the data set short description box below";
        }
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const validateStep2 = () => {
        const newErrors: Record<string, string> = {};
        if (!selected) {
            newErrors.method = "Select how you want to provide your data set";
        } else if (selected === 'link') {
            if (!link.trim()) {
                newErrors.link = "Please provide a URL link";
            }
        } else if (selected === 'file') {
            if (!file) {
                newErrors.file = "Please provide a file";
            } else {
                const fileName = file.name.toLowerCase();
                if (!fileName.endsWith('.xml') && !fileName.endsWith('.zip')) {
                    newErrors.file = "The selected file must be a TransXChange XML file or a zip file containing only TransXChange files";
                }
            }
        }
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const validateStep3 = () => {
        const newErrors: Record<string, string> = {};
        if (!consentChecked) {
            newErrors.consent = "You must confirm you have reviewed the data quality report before publishing";
        }
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const getErrorMessage = (err: unknown): string => {
        if (err instanceof ApiError) {
            if (err.code && err.code in ERROR_CODE_LOOKUP) {
                return ERROR_CODE_LOOKUP[err.code].description;
            }
            if (err.errorType === ERROR_TYPE_PII) {
                return `${ERROR_TYPE_PII}. ${NEXT_STEPS_PII}`;
            }
            if (err.errorType === ERROR_TYPE_SERVICE_CHECK) {
                return `${ERROR_TYPE_SERVICE_CHECK}. ${NEXT_STEPS_SERVICE_CHECK}`;
            }
            return err.message;
        }
        if (err instanceof Error) {
            return err.message;
        }
        return 'Upload failed. Please try again.';
    };

    const handleNext = () => {
        if (step === 1 && !validateStep1()) {
            return;
        }
        if (step === 2 && !validateStep2()) {
            return;
        }
        setErrors({});
        setStep(step + 1);
    };

    const handleSubmit = async () => {
        if (!validateStep3()) return;

        setIsSubmitting(true);
        setErrors({});

        try {
            const formData = new FormData();
            formData.append('description', dataSetDesc);
            formData.append('short_description', shortDesc);

            if (selected === 'link') {
                formData.append('url_link', link);
            } else if (selected === 'file' && file) {
                formData.append('upload_file', file);
            }

            await api.post(`/api/org/${orgId}/dataset/timetable/upload/`, formData);
            router.push(`/publish/org/${orgId}/dataset/timetable/success`);
        } catch (err) {
            setErrors({ submit: getErrorMessage(err) });
        } finally {
            setIsSubmitting(false);
        }
    };
    /* assigning classes to each step on progress bar below the header */
    const checkStep = (stepNumber: number) => {
        if (stepNumber < step) return "publish-stepper__item publish-stepper__item--previous";
        if (stepNumber === step) return "publish-stepper__item publish-stepper__item--selected";
        if (stepNumber > step) return "publish-stepper__item publish-stepper__item--next";
    }
    return(   
      <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
            <ol className="publish-stepper govuk-breadcrumbs__list">
               <li className={checkStep(1)}> 1. Describe your data set</li>
               <li className={checkStep(2)}> 2. Provide data</li>
               <li className={checkStep(3)}> 3. Set licence</li>
            </ol>
            <hr className="govuk-section-break govuk-section-break--visible" />
            <br /> <br />
            {/* part 1: Describe your data set */}
            {step === 1 && (
            <div className="govuk-grid-column-two-thirds">
                {Object.keys(errors).length > 0 && (
                    <div className="govuk-error-summary" data-module="govuk-error-summary">
                        <div role="alert">
                            <h2 className="govuk-error-summary__title">
                                There is a problem
                            </h2>
                            <div className="govuk-error-summary__body">
                                <ul className="govuk-list govuk-error-summary__list">
                                    {errors.dataSetDesc && (
                                        <li>
                                            <a href="#id_description">{errors.dataSetDesc}</a>
                                        </li>
                                    )}
                                    {errors.shortDesc && (
                                        <li>
                                            <a href="#id_short_description">{errors.shortDesc}</a>
                                        </li>
                                    )}
                                </ul>
                            </div>
                        </div>
                    </div>
                )}
                <h1 className="govuk-heading-xl">Describe your data set</h1>
                <form onSubmit={handleNext}>
                <div className={`govuk-form-group ${errors.dataSetDesc ? 'govuk-form-group--error' : ''}`}>
                    <label className="govuk-label" htmlFor="id_description"> Data Set Discription </label>
                    <div className="govuk-hint ">
                        <p> This information will give context to data consumers. 
                        Please be descriptive, but do not use personally identifiable 
                        information. </p>
                    </div>
                    {errors.dataSetDesc && (
                        <p id="id_description-error" className="govuk-error-message">
                            <span className="govuk-visually-hidden">Error:</span> {errors.dataSetDesc}
                        </p>
                    )}
                    <textarea
                    className={`govuk-textarea ${errors.dataSetDesc ? 'govuk-textarea--error' : ''}`}
                    id="id_description"
                    rows={3}
                    maxLength={300}
                    value={dataSetDesc}
                    onChange={(e) => setDataSetDesc(e.target.value)} />
                </div>
                <div className={`govuk-form-group ${errors.shortDesc ? 'govuk-form-group--error' : ''}`}>
                    <label className="govuk-label" htmlFor="id_short_description"> Dataset short description </label>
                    <div className="govuk-hint"> 
                        <p> This info will be displayed on your published data set dashboard to identify this 
                        data set and will not be visible to data set users. The maximum number of characters (with spaces) is 30 
                        characters. </p>
                    </div>
                    {errors.shortDesc && (
                        <p id="id_short_description-error" className="govuk-error-message">
                            <span className="govuk-visually-hidden">Error:</span> {errors.shortDesc}
                        </p>
                    )}
                    <input
                    className={`govuk-input ${errors.shortDesc ? 'govuk-input--error' : ''}`}
                    id="id_short_description"
                    type="text"
                    maxLength={30}
                    value={shortDesc}
                    onChange={(e) => setShortDesc(e.target.value)} />
                    <span className='govuk-hint govuk-character-count__message'>You have {30 - shortDesc.length} characters remaining.</span>
                    </div>

                <button type="button" className="govuk-button" onClick={handleNext}> Continue </button>
                </form>
            </div>
            )}

            {/* part 2: Provide data */}
            {step === 2 && (
                <div>
                    {Object.keys(errors).length > 0 && (
                        <div className="govuk-error-summary" data-module="govuk-error-summary">
                            <div role="alert">
                                <h2 className="govuk-error-summary__title">
                                    There is a problem
                                </h2>
                                <div className="govuk-error-summary__body">
                                    <ul className="govuk-list govuk-error-summary__list">
                                        {errors.method && (
                                            <li><a href="#url_link-conditional-input">{errors.method}</a></li>
                                        )}
                                        {errors.link && (
                                            <li><a href="#id_url_link">{errors.link}</a></li>
                                        )}
                                        {errors.file && (
                                            <li><a href="#id_upload_file">{errors.file}</a></li>
                                        )}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    )}
                    <h1 className="govuk-heading-xl">Choose how to provide your data set</h1>
                    <div className={`govuk-form-group ${errors.method ? 'govuk-form-group--error' : ''}`}>
                    {errors.method && (
                        <p id="method-error" className="govuk-error-message">
                            <span className="govuk-visually-hidden">Error:</span> {errors.method}
                        </p>
                    )}
                    <div className="govuk-radios" data-module="govuk-radios">
                        <div className="govuk-radios__item">
                            <input 
                            className="govuk-radios__input" 
                            id="url_link-conditional-input"
                            type="radio"
                            name="method"
                            value="link"
                            data-aria-controls="url_link-conditional"
                            checked={selected === 'link'}
                            onChange={() => setSelected('link')}
                            />
                            <label className="govuk-label govuk-radios__label" htmlFor="url_link-conditional-input"> Provide a link to your data set </label>
                        </div>

                        <div className={`govuk-radios__conditional ${selected !== 'link' ? 'govuk-radios__conditional--hidden' : ''}`} id="url_link-conditional">
                            <div className={`govuk-form-group ${errors.link ? 'govuk-form-group--error' : ''}`}>
                                <label className="govuk-label" htmlFor="id_url_link">URL Link</label>
                                <div className="govuk-hint">
                                Please provide data set URL that contains either TransXChange (see description in guidance) or zip consisting only of TransXChange files.
                                </div>
                                {errors.link && (
                                    <p id="id_url_link-error" className="govuk-error-message">
                                        <span className="govuk-visually-hidden">Error:</span> {errors.link}
                                    </p>
                                )}
                                <input
                                className={`govuk-input ${errors.link ? 'govuk-input--error' : ''}`}
                                id="id_url_link"
                                type="url"
                                value={link}
                                onChange={(e) => setLink(e.target.value)}
                                />
                            </div>
                        </div>

                        <div className="govuk-radios__item">
                            <input
                            className="govuk-radios__input"
                            id="upload_file-conditional-input"
                            type="radio"
                            name="method"
                            value="file"
                            data-aria-controls="upload_file-conditional"
                            checked={selected === 'file'}
                            onChange={() => setSelected('file')}
                            />
                            <label className="govuk-label govuk-radios__label" htmlFor="upload_file-conditional-input"> Upload data set to Bus Open Data Service </label>
                        </div>

                        <div className={`govuk-radios__conditional ${selected !== 'file' ? 'govuk-radios__conditional--hidden' : ''}`} id="upload_file-conditional">
                            <div className={`govuk-form-group ${errors.file ? 'govuk-form-group--error' : ''}`}>
                                <label className="govuk-label" htmlFor="id_upload_file">Upload File</label>
                                <div className="govuk-hint">
                                Please provide data set file that contains either TransXChange (see description in guidance) or zip consisting only of TransXChange files
                                </div>
                                {errors.file && (
                                    <p id="id_upload_file-error" className="govuk-error-message">
                                        <span className="govuk-visually-hidden">Error:</span> {errors.file}
                                    </p>
                                )}
                                <input
                                className={`govuk-input ${errors.file ? 'govuk-input--error' : ''}`}
                                id="id_upload_file"
                                type="file"
                                accept=".xml,.zip"
                                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                                />
                            </div>
                        </div>
                    </div>
                    </div>

                <br /> <br />
                <button type="button" className="govuk-button" onClick={handleNext}> Continue </button>
                </div>
            )}

            {/* part 3: Review and publish */}
            {step === 3 && (
                <div className="govuk-grid-column-two-thirds">
                    {Object.keys(errors).length > 0 && (
                        <div className="govuk-error-summary" data-module="govuk-error-summary">
                            <div role="alert">
                                <h2 className="govuk-error-summary__title">
                                    There is a problem
                                </h2>
                                <div className="govuk-error-summary__body">
                                    <ul className="govuk-list govuk-error-summary__list">
                                        {errors.consent && (
                                            <li><a href="#id_consent">{errors.consent}</a></li>
                                        )}
                                        {errors.submit && (
                                            <li>{errors.submit}</li>
                                        )}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    )}
                    <h1 className="govuk-heading-xl">Review and publish</h1>

                    <dl className="govuk-summary-list">
                        <div className="govuk-summary-list__row">
                            <dt className="govuk-summary-list__key">Data set description</dt>
                            <dd className="govuk-summary-list__value">{dataSetDesc}</dd>
                        </div>
                        <div className="govuk-summary-list__row">
                            <dt className="govuk-summary-list__key">Short description</dt>
                            <dd className="govuk-summary-list__value">{shortDesc}</dd>
                        </div>
                        <div className="govuk-summary-list__row">
                            <dt className="govuk-summary-list__key">Data provided via</dt>
                            <dd className="govuk-summary-list__value">
                                {selected === 'link' ? link : file?.name}
                            </dd>
                        </div>
                    </dl>

                    <div className={`govuk-form-group ${errors.consent ? 'govuk-form-group--error' : ''}`}>
                        <fieldset className="govuk-fieldset">
                            <legend className="govuk-fieldset__legend govuk-fieldset__legend--m">
                                Data quality confirmation
                            </legend>
                            {errors.consent && (
                                <p id="consent-error" className="govuk-error-message">
                                    <span className="govuk-visually-hidden">Error:</span> {errors.consent}
                                </p>
                            )}
                            <div className="govuk-checkboxes">
                                <div className="govuk-checkboxes__item">
                                    <input
                                        className="govuk-checkboxes__input"
                                        id="id_consent"
                                        type="checkbox"
                                        checked={consentChecked}
                                        onChange={(e) => setConsentChecked(e.target.checked)}
                                    />
                                    <label className="govuk-label govuk-checkboxes__label" htmlFor="id_consent">
                                        {hasViolations ? DATA_QUALITY_WITH_VIOLATIONS_LABEL : DATA_QUALITY_LABEL}
                                    </label>
                                </div>
                            </div>
                        </fieldset>
                    </div>

                    <button
                        type="button"
                        className="govuk-button"
                        disabled={isSubmitting}
                        onClick={handleSubmit}
                    >
                        {isSubmitting ? 'Publishing...' : 'Publish'}
                    </button>
                </div>
            )}
        </div>
      </div>
    </div>
    );
};