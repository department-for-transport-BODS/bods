import type { NextRequest } from 'next/server';
import { forwardDataFile } from '@/lib/data-file-proxy';

// Source: transit_odp/browse/views/timetable_views.py - DownloadRegionalGTFSFileView
export const dynamic = 'force-dynamic';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id } = await params;
  return forwardDataFile(request, `/timetable/download/gtfs-file/${encodeURIComponent(id)}/`);
}
