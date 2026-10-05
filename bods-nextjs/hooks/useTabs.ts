'use client';

import { useEffect, useId, useState, type AnchorHTMLAttributes, type HTMLAttributes } from 'react';

export function useTabs(tabIds: string[]) {
  const instanceId = useId();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selectedTab = tabIds.find((id) => id === selectedId) ?? tabIds[0] ?? null;

  useEffect(() => {
    const readHash = () => setSelectedId(window.location.hash.slice(1));
    readHash();
    window.addEventListener('hashchange', readHash);
    return () => window.removeEventListener('hashchange', readHash);
  }, []);

  const selectTab = (id: string) => {
    setSelectedId(id);
    window.history.replaceState(window.history.state, '', `#${id}`);
  };

  const getTabProps = (id: string): AnchorHTMLAttributes<HTMLAnchorElement> => ({
    id: `${instanceId}-${id}-tab`,
    href: `#${id}`,
    role: 'tab',
    'aria-selected': selectedTab === id,
    'aria-controls': id,
    tabIndex: selectedTab === id ? 0 : -1,
    onClick: (event) => {
      if (event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
      event.preventDefault();
      selectTab(id);
    },
    onKeyDown: (event) => {
      const index = tabIds.indexOf(id);
      let nextIndex: number;
      switch (event.key) {
        case 'ArrowLeft':
          nextIndex = (index + tabIds.length - 1) % tabIds.length;
          break;
        case 'ArrowRight':
          nextIndex = (index + 1) % tabIds.length;
          break;
        case 'Home':
          nextIndex = 0;
          break;
        case 'End':
          nextIndex = tabIds.length - 1;
          break;
        default:
          return;
      }
      const nextId = tabIds[nextIndex];
      if (!nextId) return;
      event.preventDefault();
      selectTab(nextId);
      document.getElementById(`${instanceId}-${nextId}-tab`)?.focus();
    },
  });

  const getPanelProps = (id: string): HTMLAttributes<HTMLDivElement> => ({
    id,
    role: 'tabpanel',
    'aria-labelledby': `${instanceId}-${id}-tab`,
    hidden: selectedTab !== id,
  });

  return { selectedTab, getTabProps, getPanelProps };
}