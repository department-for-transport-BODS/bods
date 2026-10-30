import type { NextRequest } from 'next/server';
import { forwardDataFile } from '@/lib/data-file-proxy';

// Source: transit_odp/browse/views/timetable_views.py - CFNDownloadBulkDataArchiveView
export const dynamic = 'force-dynamic';

export function GET(request: NextRequest): Promise<Response> {
  return forwardDataFile(request, '/timetable/download/bulk_archive/cdn');
}
