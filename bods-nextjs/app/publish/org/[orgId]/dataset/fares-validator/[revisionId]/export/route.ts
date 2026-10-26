import type { NextRequest } from 'next/server';
import { forwardPublishRoute } from '@/lib/publish-route-proxy';
import { isNumericId } from '@/lib/utils/numeric-id';

type RouteContext = {
  params: Promise<{ orgId: string; revisionId: string }>;
};

async function proxyFaresValidationExport(
  request: NextRequest,
  context: RouteContext,
): Promise<Response> {
  const { orgId, revisionId } = await context.params;

  if (!isNumericId(orgId) || !isNumericId(revisionId)) {
    return new Response(null, { status: 404 });
  }

  return forwardPublishRoute(
    request,
    `/org/${orgId}/dataset/fares-validator/${revisionId}/export/`,
  );
}

export const GET = proxyFaresValidationExport;
export const HEAD = proxyFaresValidationExport;
