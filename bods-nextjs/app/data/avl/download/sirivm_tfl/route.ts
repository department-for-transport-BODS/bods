import type { NextRequest } from 'next/server';
import { forwardDataFile } from '@/lib/data-file-proxy';

// Source: transit_odp/browse/views/avl_views.py - DownloadSIRIVMTflDataArchiveView
export const dynamic = 'force-dynamic';

export function GET(request: NextRequest): Promise<Response> {
  return forwardDataFile(request, '/avl/download/sirivm_tfl');
}
