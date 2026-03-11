"use client"; 

import { useState } from "react";

export default function CreateForm() {
    const [dataSetDesc, setDataSetDesc] = useState("");
    const [shortDesc, setShortDesc] = useState("");
    const [step, setStep] = useState(1);
    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        console.log({ dataSetDesc });
        setStep(2);
    };
    return(   
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Describe your data set</h1>
            {step === 1 && (
            <form onSubmit={handleSubmit}>
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

              <button type="submit" className="govuk-button"> Continue </button>
            </form>
            )}
            {step === 2 && (
                <p> this is step 2 </p>
            )}
          </div>
        </div>
      </div>
    </div>
    );
};