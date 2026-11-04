import type { NextRequest } from 'next/server';
import { forwardPublishRoute } from '@/lib/publish-route-proxy';
import { isNumericId } from '@/lib/utils/numeric-id';

type RouteContext = {
  params: Promise<{ orgId: string; datasetId: string }>;
};

// Django: ValidationFileDownloadView at publish
// `org/<pk1>/dataset/avl/<pk>/validation-report/` zips the live revision's recent
// SIRI validation reports. Django's status (including its 500 when no report
// exists) is passed through unchanged.
async function proxyValidationReport(request: NextRequest, context: RouteContext): Promise<Response> {
  const { orgId, datasetId } = await context.params;

  if (!isNumericId(orgId) || !isNumericId(datasetId)) {
    return new Response(null, { status: 404 });
  }

  return forwardPublishRoute(request, `/org/${orgId}/dataset/avl/${datasetId}/validation-report/`);
}

export const GET = proxyValidationReport;
export const HEAD = proxyValidationReport;
