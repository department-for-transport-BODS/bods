/**
 * Cookie Detail Page
 */

export default function CookieDetailPage() {
  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Cookie details</h1>
            <p className="govuk-body">
              Detailed information about the cookies we use on this website.
            </p>
            <h2 className="govuk-heading-l">Session cookies</h2>
            <p className="govuk-body">
              These cookies are used to maintain your session while you use the website.
            </p>
            <h2 className="govuk-heading-l">Analytics cookies</h2>
            <p className="govuk-body">
              These cookies help us understand how visitors use our website.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

