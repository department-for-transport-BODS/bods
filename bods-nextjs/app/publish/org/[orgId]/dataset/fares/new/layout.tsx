import type { Metadata } from 'next';
import type { ReactNode } from 'react';

export const metadata: Metadata = {
  title: 'Publish new data set: description',
};

export default function FaresCreateLayout({ children }: Readonly<{ children: ReactNode }>) {
  return children;
}
