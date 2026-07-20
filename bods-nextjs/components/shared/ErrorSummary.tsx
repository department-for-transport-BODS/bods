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
  className?: string;
  titleClassName?: string;
  itemClassName?: string;
  tabIndex?: number;
  dataModule?: string;
}

export function ErrorSummary({
  errors,
  title = 'There is a problem',
  summaryId = 'error-summary-title',
  className = '',
  titleClassName = '',
  itemClassName = '',
  tabIndex,
  dataModule,
}: ErrorSummaryProps) {
  if (errors.length === 0) {
    return null;
  }

  const summaryClassName = ['govuk-error-summary', className].filter(Boolean).join(' ');
  const headingClassName = ['govuk-error-summary__title', titleClassName].filter(Boolean).join(' ');

  return (
    <div
      className={summaryClassName}
      aria-labelledby={summaryId}
      role="alert"
      tabIndex={tabIndex}
      data-module={dataModule}
    >
      <h2 className={headingClassName} id={summaryId}>
        {title}
      </h2>
      <div className="govuk-error-summary__body">
        <ul className="govuk-list govuk-error-summary__list">
          {errors.map((error) => {
            if (typeof error === 'string') {
              return <li className={itemClassName} key={error}>{error}</li>;
            }

            const key = `${error.text}-${error.href || 'no-link'}`;

            return (
              <li className={itemClassName} key={key}>
                {error.href ? <a href={error.href}>{error.text}</a> : error.text}
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}