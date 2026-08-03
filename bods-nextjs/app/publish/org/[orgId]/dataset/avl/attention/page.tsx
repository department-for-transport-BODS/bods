import type { Metadata } from 'next';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { AvlAttentionContent } from '../_components/AvlAttentionContent';

export const metadata: Metadata = {
  title: 'Service Codes Requiring Attention',
};

export default function AvlAttentionPage() {
  return (
    <ProtectedRoute>
      <AvlAttentionContent />
    </ProtectedRoute>
  );
}
