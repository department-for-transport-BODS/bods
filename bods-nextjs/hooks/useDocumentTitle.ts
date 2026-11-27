'use client';

import { useEffect } from 'react';

/**
 * Sets `document.title` and keeps it while mounted. After a client-side navigation Next.js
 * mounts the route's metadata `<title>` at an unpredictable point, and the newest `<title>`
 * wins, so a one-off `document.title` assignment can be overwritten.
 */
export function useDocumentTitle(title: string) {
  useEffect(() => {
    const apply = () => {
      if (document.title !== title) document.title = title;
    };
    apply();

    const observer = new MutationObserver(apply);
    observer.observe(document.head, { childList: true, subtree: true, characterData: true });
    return () => observer.disconnect();
  }, [title]);
}
