/** @jest-environment node */

import { NextRequest } from 'next/server';
import { GET as getFaresDownload } from '@/app/publish/org/[orgId]/dataset/fares/[datasetId]/download/route';
import { GET as getFaresValidationExport } from '@/app/publish/org/[orgId]/dataset/fares-validator/[revisionId]/export/route';
import { GET as getFaresSchemaReport } from '@/app/publish/org/[orgId]/dataset/fares/[datasetId]/review/fares-csv/route';
import { forwardPublishRoute } from '@/lib/publish-route-proxy';

jest.mock('@/lib/publish-route-proxy', () => ({
  forwardPublishRoute: jest.fn(),
}));

const mockForwardPublishRoute = forwardPublishRoute as jest.Mock;

describe('fares download route proxies', () => {
  const request = new NextRequest('http://publish.localhost:3000/download');
  const proxiedResponse = new Response('download');

  beforeEach(() => {
    jest.clearAllMocks();
    mockForwardPublishRoute.mockResolvedValue(proxiedResponse);
  });

  it('forwards the fares file download to the legacy Django route', async () => {
    const response = await getFaresDownload(request, {
      params: Promise.resolve({ orgId: '1', datasetId: '9' }),
    });

    expect(response).toBe(proxiedResponse);
    expect(mockForwardPublishRoute).toHaveBeenCalledWith(
      request,
      '/org/1/dataset/fares/9/download',
    );
  });

  it('forwards the fares validation export to the legacy Django route', async () => {
    const response = await getFaresValidationExport(request, {
      params: Promise.resolve({ orgId: '1', revisionId: '42' }),
    });

    expect(response).toBe(proxiedResponse);
    expect(mockForwardPublishRoute).toHaveBeenCalledWith(
      request,
      '/org/1/dataset/fares-validator/42/export/',
    );
  });

  it('forwards the schema validation report to the legacy Django route', async () => {
    const response = await getFaresSchemaReport(request, {
      params: Promise.resolve({ orgId: '1', datasetId: '9' }),
    });

    expect(response).toBe(proxiedResponse);
    expect(mockForwardPublishRoute).toHaveBeenCalledWith(
      request,
      '/org/1/dataset/fares/9/review/fares-csv',
    );
  });

  it('does not proxy invalid Django IDs', async () => {
    const response = await getFaresDownload(request, {
      params: Promise.resolve({ orgId: '1/../account', datasetId: '9' }),
    });

    expect(response.status).toBe(404);
    expect(mockForwardPublishRoute).not.toHaveBeenCalled();
  });
});
