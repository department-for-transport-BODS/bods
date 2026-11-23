/** Full page navigation to `url`. A seam so tests can assert the target, as jsdom cannot navigate. */
export function navigateTo(url: string): void {
  globalThis.location.href = url;
}
