import type { Metadata } from 'next';
import type { ReactNode } from 'react';

export const metadata: Metadata = {
  title: 'Agent dashboard',
};

export default function AgentDashboardLayout({ children }: { children: ReactNode }) {
  return children;
}
