import type { NextRequest } from 'next/server';
import { forwardDataFile } from '@/lib/data-file-proxy';

// Source: transit_odp/browse/views/disruptions_views.py - DownloadDisruptionsGTFSRTDataArchiveView
export const dynamic = 'force-dynamic';

export function GET(request: NextRequest): Promise<Response> {
  return forwardDataFile(request, '/disruptions/download/gtfsrt_service_alerts');
}
