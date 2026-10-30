import type { NextRequest } from 'next/server';
import { forwardDataFile } from '@/lib/data-file-proxy';

// Source: transit_odp/browse/views/timetable_views.py - DownloadBulkDataArchiveRegionsView
export const dynamic = 'force-dynamic';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ regionCode: string }> },
): Promise<Response> {
  const { regionCode } = await params;
  return forwardDataFile(
    request,
    `/timetable/download/bulk_archive/${encodeURIComponent(regionCode)}`,
  );
}
