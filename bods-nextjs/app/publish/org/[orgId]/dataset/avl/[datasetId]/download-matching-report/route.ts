import type { NextRequest } from 'next/server';
import { forwardPublishRoute } from '@/lib/publish-route-proxy';
import { isNumericId } from '@/lib/utils/numeric-id';

type RouteContext = {
  params: Promise<{ orgId: string; datasetId: string }>;
};

// Django: DownloadPPCWeeklyReportView at publish
// `org/<pk1>/dataset/avl/<pk>/download-matching-report/` streams the latest weekly
// post-publishing-check report file.
async function proxyMatchingReport(request: NextRequest, context: RouteContext): Promise<Response> {
  const { orgId, datasetId } = await context.params;

  if (!isNumericId(orgId) || !isNumericId(datasetId)) {
    return new Response(null, { status: 404 });
  }

  return forwardPublishRoute(
    request,
    `/org/${orgId}/dataset/avl/${datasetId}/download-matching-report/`,
  );
}

export const GET = proxyMatchingReport;
export const HEAD = proxyMatchingReport;
