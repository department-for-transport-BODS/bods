/** @jest-environment node */

import { NextRequest } from 'next/server';
import { GET as getComplianceReport } from '@/app/data/local-authority/compliance-report/route';
import { GET as getExport, HEAD as headExport } from '@/app/data/local-authority/export/route';
import { GET as getLineLevelExport } from '@/app/data/local-authority/line-level-export/route';
import { forwardDataRoute } from '@/lib/data-route-proxy';

jest.mock('@/lib/data-route-proxy', () => ({
  forwardDataRoute: jest.fn(),
}));

const mockForwardDataRoute = forwardDataRoute as jest.Mock;

describe('local authority export route proxies', () => {
  const proxiedResponse = new Response('csv');
  const requestFor = (path: string, authIds?: string) =>
    new NextRequest(
      `http://data.localhost:3000${path}${authIds === undefined ? '' : `?auth_ids=${encodeURIComponent(authIds)}`}`,
    );

  beforeEach(() => {
    jest.clearAllMocks();
    mockForwardDataRoute.mockResolvedValue(proxiedResponse);
  });

  it.each([
    ['export', getExport, '/local-authority/export', '/local-authority/export/'],
    ['line level export', getLineLevelExport, '/local-authority/line-level-export', '/local-authority/line-level-export/'],
    ['compliance report', getComplianceReport, '/local-authority/compliance-report', '/local-authority/compliance-report/'],
  ])('forwards the %s to the Django route', async (_name, handler, path, upstream) => {
    const request = requestFor(path, '[1, 2]');

    const response = await handler(request);

    expect(response).toBe(proxiedResponse);
    expect(mockForwardDataRoute).toHaveBeenCalledWith(request, upstream);
  });

  it('forwards HEAD requests too', async () => {
    const request = requestFor('/local-authority/export', '1,2');

    await headExport(request);

    expect(mockForwardDataRoute).toHaveBeenCalledWith(request, '/local-authority/export/');
  });

  it.each([undefined, '', 'abc', '[1, x]'])('does not proxy invalid auth_ids %p', async (authIds) => {
    const response = await getExport(requestFor('/local-authority/export', authIds));

    expect(response.status).toBe(404);
    expect(mockForwardDataRoute).not.toHaveBeenCalled();
  });
});
