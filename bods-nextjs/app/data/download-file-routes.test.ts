/** @jest-environment node */

import { NextRequest } from 'next/server';
import { forwardDataFile } from '@/lib/data-file-proxy';
import { GET as timetableBulk } from './timetable/download/bulk_archive/route';
import { GET as timetableCdn } from './timetable/download/bulk_archive/cdn/route';
import { GET as timetableRegion } from './timetable/download/bulk_archive/[regionCode]/route';
import { GET as timetableCompliant } from './timetable/download/compliant_bulk_archive/route';
import { GET as timetableChange } from './timetable/download/change_archive/[publishedAt]/route';
import { GET as timetableGtfs } from './timetable/download/gtfs-file/[id]/route';
import { GET as avlBulk } from './avl/download/bulk_archive/route';
import { GET as avlGtfsrt } from './avl/download/gtfsrt/route';
import { GET as avlTfl } from './avl/download/sirivm_tfl/route';
import { GET as faresBulk } from './fares/download/bulk_archive/route';
import { GET as disruptionsBulk } from './disruptions/download/bulk_archive/route';
import { GET as disruptionsGtfsrt } from './disruptions/download/gtfsrt_service_alerts/route';

jest.mock('@/lib/data-file-proxy', () => ({
  forwardDataFile: jest.fn(),
}));

const mockForward = forwardDataFile as jest.Mock;
const request = new NextRequest('http://data.localhost:3000/x');

describe('data download file routes', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockForward.mockResolvedValue(new Response('ok'));
  });

  it.each([
    ['timetable bulk archive', timetableBulk, '/timetable/download/bulk_archive'],
    ['timetable CDN archive', timetableCdn, '/timetable/download/bulk_archive/cdn'],
    ['timetable compliant archive', timetableCompliant, '/timetable/download/compliant_bulk_archive'],
    ['AVL SIRI-VM archive', avlBulk, '/avl/download/bulk_archive'],
    ['AVL GTFS-RT', avlGtfsrt, '/avl/download/gtfsrt'],
    ['AVL TfL SIRI-VM', avlTfl, '/avl/download/sirivm_tfl'],
    ['fares archive', faresBulk, '/fares/download/bulk_archive'],
    ['disruptions SIRI-SX archive', disruptionsBulk, '/disruptions/download/bulk_archive'],
    [
      'disruptions GTFS-RT service alerts',
      disruptionsGtfsrt,
      '/disruptions/download/gtfsrt_service_alerts',
    ],
  ])('%s forwards to Django %s', async (_name, handler, upstreamPath) => {
    await (handler as (req: NextRequest) => Promise<Response>)(request);

    expect(mockForward).toHaveBeenCalledWith(request, upstreamPath);
  });

  it('forwards a regional archive by region code', async () => {
    await timetableRegion(request, { params: Promise.resolve({ regionCode: 'EA' }) });

    expect(mockForward).toHaveBeenCalledWith(request, '/timetable/download/bulk_archive/EA');
  });

  it('forwards a change archive with the trailing slash Django requires', async () => {
    await timetableChange(request, { params: Promise.resolve({ publishedAt: '2026-01-05' }) });

    expect(mockForward).toHaveBeenCalledWith(
      request,
      '/timetable/download/change_archive/2026-01-05/',
    );
  });

  it('forwards a regional GTFS file with the trailing slash Django requires', async () => {
    await timetableGtfs(request, { params: Promise.resolve({ id: 'south_east' }) });

    expect(mockForward).toHaveBeenCalledWith(request, '/timetable/download/gtfs-file/south_east/');
  });

  it('encodes path parameters so they cannot alter the upstream path', async () => {
    await timetableRegion(request, { params: Promise.resolve({ regionCode: '../x?y' }) });

    expect(mockForward).toHaveBeenCalledWith(
      request,
      '/timetable/download/bulk_archive/..%2Fx%3Fy',
    );
  });
});
