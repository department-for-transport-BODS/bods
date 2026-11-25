import { renderHook, waitFor } from '@testing-library/react';
import { useDocumentTitle } from './useDocumentTitle';

function mountMetadataTitle(text: string) {
  const title = document.createElement('title');
  title.textContent = text;
  document.head.insertBefore(title, document.head.querySelector('title'));
}

describe('useDocumentTitle', () => {
  beforeEach(() => {
    document.head.innerHTML = '';
    document.title = '';
  });

  it('keeps its title when a route metadata title mounts afterwards', async () => {
    renderHook(() => useDocumentTitle('Validating data set'));

    mountMetadataTitle('Review and publish');

    await waitFor(() => expect(document.title).toBe('Validating data set'));
  });

  it('applies title changes', () => {
    const { rerender } = renderHook(({ title }) => useDocumentTitle(title), {
      initialProps: { title: 'Validating data set' },
    });

    rerender({ title: 'Review and publish' });

    expect(document.title).toBe('Review and publish');
  });

  it('stops reasserting once unmounted', async () => {
    const { unmount } = renderHook(() => useDocumentTitle('Validating data set'));

    unmount();
    mountMetadataTitle('Next page');

    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(document.title).toBe('Next page');
  });
});
