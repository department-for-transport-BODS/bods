import { getReleaseNotes } from './release-notes';

function parseVersion(version: string): number[] {
  return version.split('.').map(Number);
}

function compareVersions(a: string, b: string): number {
  const left = parseVersion(a);
  const right = parseVersion(b);
  for (let i = 0; i < Math.max(left.length, right.length); i += 1) {
    const difference = (left[i] ?? 0) - (right[i] ?? 0);
    if (difference !== 0) {
      return difference;
    }
  }
  return 0;
}

describe('getReleaseNotes', () => {
  it('returns structured release notes, newest first', async () => {
    const releaseNotes = await getReleaseNotes();

    // The newest release is whichever has the highest version, so the test keeps
    // passing as new releases are added to the changelog data.
    const versions = releaseNotes.map((release) => release.version);
    const highestVersion = [...versions].sort((a, b) => compareVersions(b, a))[0];
    expect(releaseNotes[0].version).toBe(highestVersion);
    expect(releaseNotes.at(-1)?.version).toBe('1.14.0');

    for (let i = 1; i < versions.length; i += 1) {
      expect(compareVersions(versions[i - 1], versions[i])).toBeGreaterThan(0);
    }

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
