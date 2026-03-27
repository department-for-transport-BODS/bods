"use client"; 

import { useState } from "react";

export default function CreateForm() {
    const [dataSetDesc, setDataSetDesc] = useState("");
    const [shortDesc, setShortDesc] = useState("");
    const [step, setStep] = useState(1);
    const [selected, setSelected] = useState('');
    const [link, setLink] = useState('')
    const [file, setFile] = useState<File | null>(null)
    const [errors, setErrors] = useState<Record<string, string>>({});

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

            {/* part 3: Set licence */}
            {step === 3 && (
                <div>
                    <h1 className="govuk-heading-xl">Review and publish</h1>
                </div>
            )}
        </div>
      </div>
    </div>
    );
};