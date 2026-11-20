import 'server-only';
import { DJANGO_HOSTS, serverConfig } from '@/config/server';

export interface KnownIssue {
  description: string;
  status: 'pending' | 'fixed';
  modified: string;
}

export interface KnownIssues {
  publisher: KnownIssue[];
  consumer: KnownIssue[];
}

const NO_KNOWN_ISSUES: KnownIssues = { publisher: [], consumer: [] };

export async function getKnownIssues(): Promise<KnownIssues> {
  try {
    const wwwHost = new URL(DJANGO_HOSTS.www).host;
    const response = await fetch(
      new URL('/api/changelog/known-issues/', serverConfig.djangoInternalOrigin),
      {
        headers: { host: wwwHost, 'x-forwarded-host': wwwHost },
        cache: 'no-store',
      },
    );

    if (!response.ok) {
      console.error(`Failed to fetch known issues: ${response.status} ${response.statusText}`);
      return NO_KNOWN_ISSUES;
    }

    return (await response.json()) as KnownIssues;
  } catch (error) {
    console.error('Error fetching known issues:', error);
    return NO_KNOWN_ISSUES;
  }
}
