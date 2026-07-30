describe('public BODS hosts', () => {
  const originalBaseDomain = process.env.NEXT_PUBLIC_BODS_BASE_DOMAIN;

  afterEach(() => {
    process.env.NEXT_PUBLIC_BODS_BASE_DOMAIN = originalBaseDomain;
    jest.resetModules();
  });

  it('derives local host origins from localhost', async () => {
    process.env.NEXT_PUBLIC_BODS_BASE_DOMAIN = 'localhost';
    jest.resetModules();

    const { HOSTS } = await import('./config');

    expect(HOSTS).toEqual({
      www: 'http://localhost:8000',
      data: 'http://data.localhost:8000',
      publish: 'http://publish.localhost:8000',
      admin: 'http://admin.localhost:8000',
    });
  });

  it('derives deployed host origins from a shared base domain', async () => {
    process.env.NEXT_PUBLIC_BODS_BASE_DOMAIN = 'dev.bus-data.dft.gov.uk';
    jest.resetModules();

    const { HOSTS } = await import('./config');

    expect(HOSTS).toEqual({
      www: 'https://www.dev.bus-data.dft.gov.uk',
      data: 'https://data.dev.bus-data.dft.gov.uk',
      publish: 'https://publish.dev.bus-data.dft.gov.uk',
      admin: 'https://admin.dev.bus-data.dft.gov.uk',
    });
  });
});