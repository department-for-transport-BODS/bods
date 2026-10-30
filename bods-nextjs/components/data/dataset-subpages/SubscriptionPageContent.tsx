'use client';

/**
 * Subscribe / unsubscribe to a dataset and the success page (data host)
 *
 * Source: transit_odp/browse/templates/browse/timetables/feed_subscription.html
 *         .../feed_subscription_gatekeeper.html, .../feed_subscription_success.html
 *         (and the browse/avl overrides)
 * View: transit_odp/browse/views/{timetable,avl,fares}_views.py - *SubscriptionView,
 *       *SubscriptionSuccessView
 * API: transit_odp/browse/views/api.py - dataset_subscription_api,
 *      get_dataset_subscription_success_api
 */

import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState, type FormEvent } from 'react';
import { api } from '@/lib/api-client';
import { useFormSubmit } from '@/hooks/useFormSubmit';
import { ErrorSummary } from '@/components/shared';
import { FeedPageShell } from './FeedPageShell';
import {
  DATASET_SUBPAGE_CONFIG,
  datasetDetailHref,
  datasetSubpageApiPath,
  datasetSubpageHref,
  type DatasetSubpageKind,
} from './kinds';
import type { DatasetSubscriptionState } from './types';
import { useSubpageResource } from './useSubpageResource';

const LOAD_ERROR = 'Unable to load this page. Please refresh and try again.';

/** The page the user came from, if it is on this site; Django uses the Referer header. */
function sameSiteReferrerPath(): string {
  try {
    const referrer = new URL(document.referrer);
    return referrer.origin === window.location.origin ? `${referrer.pathname}${referrer.search}` : '';
  } catch {
    return '';
  }
}

/**
 * Anonymous visitors (Django: feed_subscription_gatekeeper.html). The template
 * says "data set" for every dataset type, AVL included.
 */
function SubscriptionGatekeeper({ backHref }: { backHref: string }) {
  return (
    <FeedPageShell backHref={backHref}>
      <div className="govuk-grid-row">
        <div className="govuk-grid-column-full">
          <h1 className="govuk-heading-l">Get data set updates</h1>
          <p className="govuk-body-l">
            Please sign in to receive email notifications. You will be able to subscribe to data set updates and
            manage these in your account.
          </p>
          <a role="button" className="govuk-button" href="/account/login/">
            Sign in
          </a>
          <p className="govuk-body">
            Don&apos;t have an account?{' '}
            <a className="govuk-link" href="/account/signup/">
              Create account
            </a>
          </p>
        </div>
      </div>
    </FeedPageShell>
  );
}

function SubscriptionForm({ kind, state, cancelHref }: { kind: DatasetSubpageKind; state: DatasetSubscriptionState; cancelHref: string }) {
  const router = useRouter();
  const datasetId = String(state.datasetId);
  const { noun } = DATASET_SUBPAGE_CONFIG[kind];
  const { isSubmitting, submitError, handleSubmit } = useFormSubmit();
  const verb = state.isSubscribed ? 'Unsubscribe from' : 'Subscribe to';

  useEffect(() => {
    document.title = `${verb} ${noun}`;
  }, [verb, noun]);

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void handleSubmit(async () => {
      await api.post(datasetSubpageApiPath(kind, datasetId, 'subscription'), {});
      router.push(datasetSubpageHref(kind, datasetId, 'subscription/success'));
    });
  };

  return (
    <FeedPageShell backHref={cancelHref}>
      <ErrorSummary errors={submitError ? [submitError] : []} />
      <form onSubmit={onSubmit} noValidate>
        <div className="govuk-grid-row">
          <h1 className="govuk-heading-xl">{`${verb} ${noun}`}</h1>
          <p className="govuk-body">
            Would you like to {state.isSubscribed ? 'unsubscribe from' : 'subscribe to'} {state.name} {noun}?
          </p>
          <div className="button-holder">
            <button type="submit" name="submit" value="submit" className="govuk-button" data-module="govuk-button" disabled={isSubmitting}>
              Confirm
            </button>
            <a className="govuk-button govuk-button--secondary" href={cancelHref}>
              Cancel
            </a>
          </div>
        </div>
      </form>
    </FeedPageShell>
  );
}

export function SubscriptionPageContent({ kind }: { kind: DatasetSubpageKind }) {
  const datasetId = useParams().id as string;
  // The Cancel link and the success page return to wherever the user came from.
  // Only read once the page has loaded, so it never reaches the server render.
  const [backPath] = useState(() => (typeof document === 'undefined' ? '' : sameSiteReferrerPath()));
  const base = datasetSubpageApiPath(kind, datasetId, 'subscription');
  const apiPath = backPath ? `${base}?backPath=${encodeURIComponent(backPath)}` : base;

  const { data, error } = useSubpageResource<DatasetSubscriptionState>(apiPath, LOAD_ERROR);
  const detailHref = datasetDetailHref(kind, datasetId);

  if (!data) return <FeedPageShell backHref={detailHref} error={error} />;

  if (!data.isAuthenticated) {
    return <SubscriptionGatekeeper backHref={detailHref} />;
  }

  return <SubscriptionForm kind={kind} state={data} cancelHref={backPath || detailHref} />;
}

export function SubscriptionSuccessPageContent({ kind }: { kind: DatasetSubpageKind }) {
  const datasetId = useParams().id as string;
  const { noun } = DATASET_SUBPAGE_CONFIG[kind];
  const { data, error } = useSubpageResource<DatasetSubscriptionState>(
    datasetSubpageApiPath(kind, datasetId, 'subscription/success'),
    LOAD_ERROR,
  );

  useEffect(() => {
    if (data?.isAuthenticated) {
      document.title = data.isSubscribed ? 'Subscribed successfully' : 'Unsubscribed successfully';
    }
  }, [data]);

  if (!data) return <FeedPageShell error={error} />;

  if (!data.isAuthenticated) {
    return <SubscriptionGatekeeper backHref={datasetDetailHref(kind, datasetId)} />;
  }

  return (
    <FeedPageShell>
      <div className="govuk-grid-row">
        <div className="govuk-grid-column-two-thirds">
          <h1 className="govuk-heading-xl">
            {data.isSubscribed
              ? `You have successfully subscribed to the ${noun}`
              : `You will no longer receive notification on the ${noun}`}
          </h1>
          <a role="button" className="govuk-button" href={data.backPath}>
            {data.backButtonText}
          </a>
        </div>
      </div>
    </FeedPageShell>
  );
}
