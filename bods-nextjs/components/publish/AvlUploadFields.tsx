type AvlUploadFieldErrors = {
  urlLink?: string;
  username?: string;
  password?: string;
  requestorRef?: string;
};

type AvlUploadFieldsProps = {
  urlLink: string;
  username: string;
  password: string;
  requestorRef: string;
  errors?: AvlUploadFieldErrors;
  onUrlLinkChange: (value: string) => void;
  onUsernameChange: (value: string) => void;
  onPasswordChange: (value: string) => void;
  onRequestorRefChange: (value: string) => void;
  ipAllowListHint?: string;
};

export function AvlUploadFields({
  urlLink,
  username,
  password,
  requestorRef,
  errors,
  onUrlLinkChange,
  onUsernameChange,
  onPasswordChange,
  onRequestorRefChange,
  ipAllowListHint,
}: AvlUploadFieldsProps) {
  return (
    <>
      <div className={`govuk-form-group ${errors?.urlLink ? 'govuk-form-group--error' : ''}`}>
        <label className="govuk-label" htmlFor="id_url_link">
          Provide a URL link
        </label>
        <div className="govuk-hint">
          We have guidance on the SIRI-VM standard and how to provide data.
        </div>
        {errors?.urlLink && <p className="govuk-error-message">{errors.urlLink}</p>}
        <input
          className="govuk-input govuk-!-width-three-quarters"
          id="id_url_link"
          type="url"
          value={urlLink}
          onChange={(event) => onUrlLinkChange(event.target.value)}
        />
      </div>

      <div className={`govuk-form-group ${errors?.username ? 'govuk-form-group--error' : ''}`}>
        <label className="govuk-label" htmlFor="id_username">
          Username
        </label>
        {errors?.username && <p className="govuk-error-message">{errors.username}</p>}
        <input
          className="govuk-input govuk-!-width-three-quarters"
          id="id_username"
          type="text"
          value={username}
          onChange={(event) => onUsernameChange(event.target.value)}
        />
      </div>

      <div className={`govuk-form-group ${errors?.password ? 'govuk-form-group--error' : ''}`}>
        <label className="govuk-label" htmlFor="id_password">
          Password
        </label>
        {errors?.password && <p className="govuk-error-message">{errors.password}</p>}
        <input
          className="govuk-input govuk-!-width-three-quarters"
          id="id_password"
          type="password"
          value={password}
          onChange={(event) => onPasswordChange(event.target.value)}
        />
      </div>

      <div className={`govuk-form-group ${errors?.requestorRef ? 'govuk-form-group--error' : ''}`}>
        <label className="govuk-label" htmlFor="id_requestor_ref">
          RequestorRef (Optional)
        </label>
        {errors?.requestorRef && <p className="govuk-error-message">{errors.requestorRef}</p>}
        <input
          className="govuk-input govuk-!-width-three-quarters"
          id="id_requestor_ref"
          type="text"
          value={requestorRef}
          onChange={(event) => onRequestorRefChange(event.target.value)}
        />
      </div>

      {ipAllowListHint && (
        <span className="govuk-hint">
          If you require your SIRI-VM feed to be restricted to particular IP addresses, please
          allow-list these IP addresses: {ipAllowListHint}
        </span>
      )}
    </>
  );
}
