export function queryWith(
  params: { toString(): string },
  updates: Record<string, string>,
): string {
  const next = new URLSearchParams(params.toString());
  for (const [key, value] of Object.entries(updates)) {
    next.set(key, value);
  }
  return `?${next.toString()}`;
}
