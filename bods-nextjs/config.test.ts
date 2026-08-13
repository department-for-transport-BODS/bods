describe('public BODS hosts', () => {
  const originalBaseDomain = process.env.NEXT_PUBLIC_BODS_BASE_DOMAIN;
  const originalPort = process.env.NEXT_PUBLIC_BODS_PORT;
  const originalDjangoOrigin = process.env.DJANGO_INTERNAL_ORIGIN;

  afterEach(() => {
    process.env.NEXT_PUBLIC_BODS_BASE_DOMAIN = originalBaseDomain;
    process.env.NEXT_PUBLIC_BODS_PORT = originalPort;
    process.env.DJANGO_INTERNAL_ORIGIN = originalDjangoOrigin;
    jest.resetModules();
  });

  it('derives local host origins from localhost', async () => {
    process.env.NEXT_PUBLIC_BODS_BASE_DOMAIN = 'localhost';
    process.env.NEXT_PUBLIC_BODS_PORT = '3000';
    jest.resetModules();

    const { HOSTS } = await import('./config/client');

    expect(HOSTS).toEqual({
      www: 'http://localhost:3000',
      data: 'http://data.localhost:3000',
      publish: 'http://publish.localhost:3000',
      admin: 'http://admin.localhost:3000',
    });
  });

  it('derives deployed host origins from a shared base domain', async () => {
    process.env.NEXT_PUBLIC_BODS_BASE_DOMAIN = 'dev.bus-data.dft.gov.uk';
    delete process.env.NEXT_PUBLIC_BODS_PORT;
    jest.resetModules();

    const { HOSTS } = await import('./config/client');

    expect(HOSTS).toEqual({
      www: 'https://www.dev.bus-data.dft.gov.uk',
      data: 'https://data.dev.bus-data.dft.gov.uk',
      publish: 'https://publish.dev.bus-data.dft.gov.uk',
      admin: 'https://admin.dev.bus-data.dft.gov.uk',
    });
  });

  it('defaults the local frontend port to 3000', async () => {
    process.env.NEXT_PUBLIC_BODS_BASE_DOMAIN = 'localhost';
    delete process.env.NEXT_PUBLIC_BODS_PORT;
    jest.resetModules();

    const { HOSTS } = await import('./config/client');

    expect(HOSTS.www).toBe('http://localhost:3000');
    expect(HOSTS.publish).toBe('http://publish.localhost:3000');
  });

  it('keeps Django upstream hosts on the Django port locally', async () => {
    process.env.NEXT_PUBLIC_BODS_BASE_DOMAIN = 'localhost';
    process.env.NEXT_PUBLIC_BODS_PORT = '3000';
    process.env.DJANGO_INTERNAL_ORIGIN = 'http://localhost:8000';
    jest.resetModules();

    const { DJANGO_HOSTS } = await import('./config/server');

    expect(DJANGO_HOSTS).toEqual({
      www: 'http://localhost:8000',
      data: 'http://data.localhost:8000',
      publish: 'http://publish.localhost:8000',
      admin: 'http://admin.localhost:8000',
    });
  });
});