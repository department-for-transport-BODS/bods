interface ErrorSummaryProps {
  errors: string[];
  title?: string;
  summaryId?: string;
}

export function ErrorSummary({
  errors,
  title = 'There is a problem',
  summaryId = 'error-summary-title',
}: ErrorSummaryProps) {
  if (errors.length === 0) {
    return null;
  }

  return (
    <div className="govuk-error-summary" aria-labelledby={summaryId} role="alert">
      <h2 className="govuk-error-summary__title" id={summaryId}>
        {title}
      </h2>
      <div className="govuk-error-summary__body">
        <ul className="govuk-list govuk-error-summary__list">
          {errors.map((error) => (
            <li key={error}>{error}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}