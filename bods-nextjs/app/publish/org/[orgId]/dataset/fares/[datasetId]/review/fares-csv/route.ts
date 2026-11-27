import type { NextRequest } from 'next/server';
import { forwardPublishRoute } from '@/lib/publish-route-proxy';
import { isNumericId } from '@/lib/utils/numeric-id';

type RouteContext = {
  params: Promise<{ orgId: string; datasetId: string }>;
};

async function proxyFaresSchemaReport(request: NextRequest, context: RouteContext): Promise<Response> {
  const { orgId, datasetId } = await context.params;

  if (!isNumericId(orgId) || !isNumericId(datasetId)) {
    return new Response(null, { status: 404 });
  }

  return forwardPublishRoute(
    request,
    `/org/${orgId}/dataset/fares/${datasetId}/review/fares-csv`,
  );
}

export const GET = proxyFaresSchemaReport;
export const HEAD = proxyFaresSchemaReport;
