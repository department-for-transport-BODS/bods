/** Full page reload. A seam so tests can assert it, as jsdom cannot navigate. */
export function reloadPage(): void {
  window.location.reload();
}
