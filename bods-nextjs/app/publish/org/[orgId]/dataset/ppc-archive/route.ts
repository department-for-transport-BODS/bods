import type { NextRequest } from 'next/server';
import { forwardPublishRoute } from '@/lib/publish-route-proxy';
import { isNumericId } from '@/lib/utils/numeric-id';

type RouteContext = {
  params: Promise<{ orgId: string }>;
};

// Django: PPCArchiveView at publish `org/<pk1>/dataset/ppc-archive/` streams
// archived_avl_to_timetable_matching_all_feeds.zip.
async function proxyPpcArchive(request: NextRequest, context: RouteContext): Promise<Response> {
  const { orgId } = await context.params;

  if (!isNumericId(orgId)) {
    return new Response(null, { status: 404 });
  }

  return forwardPublishRoute(request, `/org/${orgId}/dataset/ppc-archive/`);
}

export const GET = proxyPpcArchive;
export const HEAD = proxyPpcArchive;
