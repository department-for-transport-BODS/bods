import {
  bodsAreaFromHostname,
  buildBodsHosts,
  hostPath,
  hostnameFromHeaders,
  isAllowedBodsHostname,
} from './hosts';

describe('host helpers', () => {
  it('builds local and deployed origins', () => {
    expect(buildBodsHosts('localhost', '3000')).toEqual({
      www: 'http://localhost:3000',
      data: 'http://data.localhost:3000',
      publish: 'http://publish.localhost:3000',
      admin: 'http://admin.localhost:3000',
    });

    expect(buildBodsHosts('dev.bus-data.dft.gov.uk', '')).toEqual({
      www: 'https://www.dev.bus-data.dft.gov.uk',
      data: 'https://data.dev.bus-data.dft.gov.uk',
      publish: 'https://publish.dev.bus-data.dft.gov.uk',
      admin: 'https://admin.dev.bus-data.dft.gov.uk',
    });
  });

  it('joins an origin and path without duplicating slashes', () => {
    expect(hostPath('http://localhost:3000', '/')).toBe('http://localhost:3000');
    expect(hostPath('http://data.localhost:3000', '/timetables?status=live')).toBe(
      'http://data.localhost:3000/timetables?status=live',
    );
    expect(hostPath('https://www.example.com', '?status=live')).toBe(
      'https://www.example.com?status=live',
    );
  });

  it('maps hostnames to BODS areas', () => {
    expect(bodsAreaFromHostname('localhost:3000')).toBe('www');
    expect(bodsAreaFromHostname('publish.localhost:3000')).toBe('publish');
    expect(bodsAreaFromHostname('www.dev.bus-data.dft.gov.uk')).toBe('www');
    expect(bodsAreaFromHostname('data.dev.bus-data.dft.gov.uk')).toBe('data');
  });

  it('allow-lists known BODS hosts', () => {
    expect(isAllowedBodsHostname('data.localhost:3000', 'localhost')).toBe(true);
    expect(isAllowedBodsHostname('publish.xyz.com', 'xyz.com')).toBe(true);
    expect(isAllowedBodsHostname('xyz.com', 'xyz.com')).toBe(true);
    expect(isAllowedBodsHostname('publish.evil.com', 'xyz.com')).toBe(false);
  });

  it('prefers Host over X-Forwarded-Host', () => {
    expect(hostnameFromHeaders('publish.xyz.com', 'publish.evil.com')).toBe('publish.xyz.com');
    expect(hostnameFromHeaders(null, 'data.localhost:3000')).toBe('data.localhost:3000');
  });
});
