import type { NextRequest } from 'next/server';
import { forwardPublishRoute } from '@/lib/publish-route-proxy';
import { isNumericId } from '@/lib/utils/numeric-id';

type RouteContext = {
  params: Promise<{ orgId: string }>;
};

async function proxyComplianceReportCsv(request: NextRequest, context: RouteContext): Promise<Response> {
  const { orgId } = await context.params;

  if (!isNumericId(orgId)) {
    return new Response(null, { status: 404 });
  }

  return forwardPublishRoute(request, `/org/${orgId}/dataset/timetable/compliance-report/`);
}

export const GET = proxyComplianceReportCsv;
export const HEAD = proxyComplianceReportCsv;
