import { dataApiPath } from './api-paths';

describe('dataApiPath', () => {
  it.each([
    ['/api/v1/dataset/', '/api/data/v1/dataset/'],
    ['/api/v2/timetables/', '/api/data/v2/timetables/'],
    ['/v1/service_pattern/', '/api/data/v1/service_pattern/'],
  ])('maps %s to %s', (djangoPath, gatewayPath) => {
    expect(dataApiPath(djangoPath)).toBe(gatewayPath);
  });
});