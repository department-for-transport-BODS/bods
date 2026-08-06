export function dataApiPath(djangoApiPath: string): string {
  const upstreamPath = djangoApiPath.replace(/^\/api(?=\/)/, '');
  return `/api/data${upstreamPath}`;
}