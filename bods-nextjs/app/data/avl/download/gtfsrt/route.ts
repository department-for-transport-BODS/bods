import type { NextRequest } from 'next/server';
import { forwardDataFile } from '@/lib/data-file-proxy';

// Source: transit_odp/browse/views/avl_views.py - DownloadGTFSRTDataArchiveView
export const dynamic = 'force-dynamic';

export function GET(request: NextRequest): Promise<Response> {
  return forwardDataFile(request, '/avl/download/gtfsrt');
}
