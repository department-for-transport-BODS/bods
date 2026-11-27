import type { NextRequest } from 'next/server';
import { forwardDataFile } from '@/lib/data-file-proxy';

// Source: transit_odp/browse/views/timetable_views.py - DownloadChangeDataArchiveView
export const dynamic = 'force-dynamic';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ publishedAt: string }> },
): Promise<Response> {
  const { publishedAt } = await params;
  return forwardDataFile(
    request,
    `/timetable/download/change_archive/${encodeURIComponent(publishedAt)}/`,
  );
}
