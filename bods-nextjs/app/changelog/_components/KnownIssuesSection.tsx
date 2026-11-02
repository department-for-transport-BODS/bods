import type { KnownIssue, KnownIssues } from '@/lib/changelog/known-issues';

function IssueList({ issues }: { issues: KnownIssue[] }) {
  return (
    <ul className="govuk-list govuk-list--bullet govuk-!-margin-bottom-8">
      {issues.map((issue) => (
        <li key={`${issue.modified}-${issue.description}`} className="govuk-!-margin-bottom-3">
          {issue.status === 'fixed' && (
            <>
              <strong className="govuk-tag govuk-tag--green">Fixed</strong>{' '}
            </>
          )}
          {issue.description}
        </li>
      ))}
    </ul>
  );
}

export function KnownIssuesSection({ knownIssues }: { knownIssues: KnownIssues }) {
  const { publisher, consumer } = knownIssues;

  if (publisher.length === 0 && consumer.length === 0) {
    return null;
  }

  return (
    <>
      <hr className="govuk-section-break govuk-section-break--l govuk-section-break--visible" />
      <div className="govuk-grid-row">
        <div className="govuk-grid-column-full">
          <h2 className="govuk-heading-l">Known Issues</h2>
          {publisher.length > 0 && (
            <>
              <h3 className="govuk-heading-m govuk-!-margin-bottom-7">Publisher issues:</h3>
              <IssueList issues={publisher} />
            </>
          )}
          {consumer.length > 0 && (
            <>
              <h3 className="govuk-heading-m govuk-!-margin-bottom-7">Consumer issues:</h3>
              <IssueList issues={consumer} />
            </>
          )}
        </div>
      </div>
    </>
  );
}
