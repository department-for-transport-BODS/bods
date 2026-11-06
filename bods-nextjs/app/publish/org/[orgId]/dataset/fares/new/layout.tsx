import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Publish new data set: description',
};

export default function FaresCreateLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <>{children}</>;
}
