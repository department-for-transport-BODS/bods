/**
 * Server-side fetch of a data-host dataset detail payload from Django
 * (`/api/browser/{timetables,avl,fares}/<id>/`), shared by the timetable, AVL
 * and fares detail pages.
 *
 * Resolves to null only when Django says 404 (unknown, not published, inactive
 * publisher or the wrong dataset type). Any other failure throws, so it
 * surfaces as a 500 like Django's.
 */

import { headers } from 'next/headers';
import { DJANGO_HOSTS, serverConfig } from '@/config/server';

export type DatasetDetailApiKind = 'timetables' | 'avl' | 'fares';

export async function fetchDatasetDetail<T>(kind: DatasetDetailApiKind, id: string): Promise<T | null> {
  const url = new URL(`/api/browser/${kind}/${encodeURIComponent(id)}/`, serverConfig.djangoInternalOrigin);
  const requestHeaders = await headers();
  const upstreamHeaders = new Headers();
  const cookie = requestHeaders.get('cookie');
  if (cookie) {
    upstreamHeaders.set('cookie', cookie);
  }
  const dataHost = new URL(DJANGO_HOSTS.data).host;
  upstreamHeaders.set('host', dataHost);
  upstreamHeaders.set('x-forwarded-host', dataHost);

  const response = await fetch(url, {
    method: 'GET',
    headers: upstreamHeaders,
    cache: 'no-store',
  });

  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`Failed to fetch ${kind} dataset ${id}: ${response.status} ${response.statusText}`);
  }

  return (await response.json()) as T;
}
