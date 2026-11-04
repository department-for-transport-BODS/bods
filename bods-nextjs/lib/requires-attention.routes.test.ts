/** @jest-environment node */

import { NextRequest } from 'next/server';
import { GET as getComplianceReport, HEAD as headComplianceReport } from '@/app/publish/org/[orgId]/dataset/timetable/compliance-report/route';
import { GET as getServiceCodes, HEAD as headServiceCodes } from '@/app/publish/org/[orgId]/dataset/timetable/service-codes/route';
import { forwardPublishRoute } from '@/lib/publish-route-proxy';

jest.mock('@/lib/publish-route-proxy', () => ({
  forwardPublishRoute: jest.fn(),
}));

const mockForwardPublishRoute = forwardPublishRoute as jest.Mock;

describe('timetable requires-attention CSV route proxies', () => {
  const request = new NextRequest('http://publish.localhost:3000/export');
  const proxiedResponse = new Response('csv');

  beforeEach(() => {
    jest.clearAllMocks();
    mockForwardPublishRoute.mockResolvedValue(proxiedResponse);
  });

  it('forwards the service codes CSV to the Django route', async () => {
    const response = await getServiceCodes(request, { params: Promise.resolve({ orgId: '7' }) });

    expect(response).toBe(proxiedResponse);
    expect(mockForwardPublishRoute).toHaveBeenCalledWith(request, '/org/7/dataset/timetable/service-codes/');
  });

  it('forwards the compliance report CSV to the Django route', async () => {
    const response = await getComplianceReport(request, { params: Promise.resolve({ orgId: '7' }) });

    expect(response).toBe(proxiedResponse);
    expect(mockForwardPublishRoute).toHaveBeenCalledWith(request, '/org/7/dataset/timetable/compliance-report/');
  });

  it('supports HEAD requests', async () => {
    await headServiceCodes(request, { params: Promise.resolve({ orgId: '7' }) });
    await headComplianceReport(request, { params: Promise.resolve({ orgId: '7' }) });

    expect(mockForwardPublishRoute).toHaveBeenCalledTimes(2);
  });

  it.each([
    ['service codes', getServiceCodes],
    ['compliance report', getComplianceReport],
  ])('does not proxy invalid organisation IDs for the %s CSV', async (_name, handler) => {
    const response = await handler(request, { params: Promise.resolve({ orgId: '7/../account' }) });

    expect(response.status).toBe(404);
    expect(mockForwardPublishRoute).not.toHaveBeenCalled();
  });
});
