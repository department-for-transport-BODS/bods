import { Fragment } from 'react';
import type { ReleaseNote } from '@/lib/changelog/release-notes';

function formatReleaseMonth(date: string): string {
  return new Intl.DateTimeFormat('en-GB', {
    month: 'long',
    year: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(`${date}-01T00:00:00Z`));
}

function InlineText({ text }: { text: string }) {
  return (
    <>
      {text.split('`').map((part, index) =>
        index % 2 === 1 ? <code key={index}>{part}</code> : part,
      )}
    </>
  );
}

export function ReleaseNotesSection({ releaseNotes }: { releaseNotes: ReleaseNote[] }) {
  return (
    <>
      {releaseNotes.map((release) => (
        <Fragment key={release.version}>
          <h3 className="govuk-heading-m govuk-!-margin-bottom-5">
            {formatReleaseMonth(release.date)} ({release.version})
          </h3>
          {release.summary && (
            <p className="govuk-body govuk-!-font-size-19">{release.summary}</p>
          )}
          {release.items.length > 0 && (
            <ul className="govuk-list govuk-list--bullet">
              {release.items.map((item, index) => (
                <li key={index}>
                  <InlineText text={item} />
                </li>
              ))}
            </ul>
          )}
        </Fragment>
      ))}
    </>
  );
}
