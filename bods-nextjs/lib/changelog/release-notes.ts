import releaseNotesFile from '@/content/changelog/release-notes.json';

export interface ReleaseNote {
  version: string;
  /** Release month in `YYYY-MM` format. */
  date: string;
  summary?: string;
  /** Plain text; wrap inline code in backticks. */
  items: string[];
}

/**
 * Single source for release notes. Page components must only use this loader,
 * so moving the notes to external hosting (e.g. S3) only means changing this function.
 */
export async function getReleaseNotes(): Promise<ReleaseNote[]> {
  return releaseNotesFile.releases;
}
