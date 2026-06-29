import { redirect } from 'next/navigation';

type AvlFeedDetailRedirectPageProps = {
  params: Promise<{
    orgId: string;
  }>;
};

export default async function AvlFeedDetailRedirectPage({ params }: AvlFeedDetailRedirectPageProps) {
  const { orgId } = await params;
  redirect(`/publish/org/${orgId}/dataset/avl/`);
}
