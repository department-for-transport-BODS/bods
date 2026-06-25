type ErrorSummaryItem =
  | string
  | {
      text: string;
      href?: string;
    };

interface ErrorSummaryProps {
  errors: ErrorSummaryItem[];
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
          {errors.map((error) => {
            if (typeof error === 'string') {
              return <li key={error}>{error}</li>;
            }

            const key = `${error.text}-${error.href || 'no-link'}`;

            return (
              <li key={key}>
                {error.href ? <a href={error.href}>{error.text}</a> : error.text}
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}