/**
 * AVL Feed Management Page
 * 
 * Manage AVL (Automatic Vehicle Location) feeds
 */

'use client';

import { useState, useEffect } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { getPaginated } from '@/lib/api-client';
import { useParams } from 'next/navigation';
import Link from 'next/link';

interface AVLFeed {
  id: number;
  name: string;
  url: string;
  status: string;
}

function AVLManagement() {
  const params = useParams();
  const orgId = params.orgId as string;
  const [feeds, setFeeds] = useState<AVLFeed[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadFeeds();
  }, [orgId]);

  const loadFeeds = async () => {
    try {
      const data = await getPaginated<AVLFeed>(`/api/org/${orgId}/avl/feeds/`);
      setFeeds(data.results);
    } catch (err) {
      console.error('Failed to load AVL feeds', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-full">
            <h1 className="govuk-heading-xl">AVL feeds</h1>
            <Link href={`/publish/org/${orgId}/dataset/avl/new`} className="govuk-button">
              Add new feed
            </Link>

            {isLoading ? (
              <p className="govuk-body">Loading feeds...</p>
            ) : (
              <table className="govuk-table">
                <thead className="govuk-table__head">
                  <tr className="govuk-table__row">
                    <th className="govuk-table__header">Name</th>
                    <th className="govuk-table__header">URL</th>
                    <th className="govuk-table__header">Status</th>
                    <th className="govuk-table__header">Actions</th>
                  </tr>
                </thead>
                <tbody className="govuk-table__body">
                  {feeds.map((feed) => (
                    <tr key={feed.id} className="govuk-table__row">
                      <td className="govuk-table__cell">{feed.name}</td>
                      <td className="govuk-table__cell">{feed.url}</td>
                      <td className="govuk-table__cell">{feed.status}</td>
                      <td className="govuk-table__cell">
                        <Link href={`/publish/org/${orgId}/dataset/avl/${feed.id}`} className="govuk-link">
                          Manage
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AVLPage() {
  return (
    <ProtectedRoute>
      <AVLManagement />
    </ProtectedRoute>
  );
}

