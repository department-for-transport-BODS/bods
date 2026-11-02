import { getReleaseNotes } from './release-notes';

describe('getReleaseNotes', () => {
  it('returns structured release notes, newest first', async () => {
    const releaseNotes = await getReleaseNotes();

    expect(releaseNotes[0].version).toBe('1.60.0');
    expect(releaseNotes.at(-1)?.version).toBe('1.14.0');

    const dates = releaseNotes.map((release) => release.date);
    expect(dates).toEqual([...dates].sort().reverse());

    releaseNotes.forEach((release) => {
      expect(release.version).toMatch(/^\d+\.\d+/);
      expect(release.date).toMatch(/^\d{4}-(0[1-9]|1[0-2])$/);
      expect(Array.isArray(release.items)).toBe(true);
      expect(release.summary || release.items.length).toBeTruthy();
    });
  });

  it('has unique versions', async () => {
    const versions = (await getReleaseNotes()).map((release) => release.version);

    expect(new Set(versions).size).toBe(versions.length);
  });
});
