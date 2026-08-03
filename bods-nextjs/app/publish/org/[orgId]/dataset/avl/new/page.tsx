import type { Metadata } from 'next';
import { connection } from 'next/server';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { config } from '@/runtime-config';
import { AVLCreatePageContent } from '../_components/AVLCreatePageContent';

export const metadata: Metadata = {
  title: 'Publish new data feed',
};

export default async function AVLCreatePage() {
  await connection();

  return (
    <ProtectedRoute>
      <AVLCreatePageContent avlIpAllowList={config.avlIpAllowList} />
    </ProtectedRoute>
  );
}
