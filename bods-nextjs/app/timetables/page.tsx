"use client"; 

import { useState } from "react";

export default function CreateForm() {
    const [dataSetDesc, setDataSetDesc] = useState("");
    const [shortDesc, setShortDesc] = useState("");
    const [step, setStep] = useState(1);
    const [selected, setSelected] = useState('');
    const [link, setLink] = useState('')
    const [file,setFile] = useState('')
    const handleNext = () => {
        console.log({ dataSetDesc });
        setStep(step + 1);
    };
    return(   
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
            {step === 1 && (
            <div className="govuk-grid-column-two-thirds">
                <h1 className="govuk-heading-xl">Describe your data set</h1>
                <form onSubmit={handleNext}>
                <div className="govuk-form-group">
                    <label className="govuk-label" htmlFor="dataSetDesc"> Data Set Discription </label>
                    <div className="govuk-hint ">
                        <p> This information will give context to data consumers. 
                        Please be descriptive, but do not use personally identifiable 
                        information. </p>
                    </div> 
                    <textarea
                    className="govuk-textarea"
                    id="dataSetDesc"
                    rows={3}
                    value={dataSetDesc}
                    onChange={(e) => setDataSetDesc(e.target.value)} />
                </div>

                <div className="govuk-form-group">
                    <label className="govuk-label" htmlFor="shortDesc"> Dataset short description </label>
                    <div className="govuk-hint"> 
                        <p> This info will be displayed on your published data set dashboard to identify this 
                        data set and will not be visible to data set users. The maximum number of characters (with spaces) is 30 
                        characters. </p>
                    </div>
                    <input
                    className="govuk-input"
                    id="shortDesc"
                    type="text"
                    value={shortDesc}
                    onChange={(e) => setShortDesc(e.target.value)} />
                    </div>

                <button type="button" className="govuk-button" onClick={handleNext}> Continue </button>
                </form>
            </div>
            )}
            {step === 2 && (
                <div>
                    <h1 className="govuk-heading-xl">Choose how to provide your data set</h1>
                    <div className="govuk-radios">
                        <div className="govuk-radios__item">
                            <input 
                            className="govuk-radios__input"
                            type="radio"
                            name="method"
                            value="link"
                            checked={selected === 'link'}           // true only when 'selected' equals 'link'
                            onChange={() => setSelected('link')}    // updates state when this radio is clicked
                            />
                            <label className="govuk-radios__label"> Provide a link to your data set </label>
                        </div>

                    
                        <div className="govuk-radios__item">
                            <input
                            className="govuk-radios__input"
                            type="radio"
                            name="method"
                            value="file"
                            checked={selected === 'file'}
                            onChange={() => setSelected('file')}
                            />
                            <label className="govuk-radios__label"> Upload data set to Bus Open Data Service </label>
                        </div>
                </div>
                    {selected === 'link' && (
                        <input
                        className="govuk-input"
                        id="link"
                        type="url"
                        value={link}
                        onChange={(e) => setLink(e.target.value)} />
                    )}

                    {selected === 'file' && (
                        <input
                        className="govuk-input"
                        id="file"
                        type="file"
                        value={file}
                        onChange={(e) => setFile(e.target.value)} />
                    )} 
                <button type="button" className="govuk-button" onClick={handleNext}> Continue </button>
                </div>
            )}
            {/* {step === 3 && (

            )} */}
        </div>
      </div>
    </div>
    );
};