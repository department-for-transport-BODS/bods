'use client';

import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faPlay } from '@fortawesome/free-solid-svg-icons';
import { publishAppPath } from '@/config/client';
import { AvlMatchingHelpModal } from '@/components/publish/AvlMatchingHelpModal';
import { REVIEW_LIST_KINDS, reviewListPath } from './reviewListConfig';
import type {
  AvlBanner,
  FaresBanner,
  ReviewListBanner,
  ReviewListKind,
  TimetableBanner,
} from './types';

interface ReviewStatProps {
  top: React.ReactNode;
  bottom?: string;
  description: string;
  link?: { href: string; label: string };
}

function ReviewStat({ top, bottom, description, link }: ReviewStatProps) {
  return (
    <div className="review-stat">
      <div>
        <span className="review-stat__top">{top}</span>
        {bottom !== undefined && <span className="review-stat__bottom">{bottom}</span>}
      </div>
      <p className="review-stat__description">{description}</p>
      {link && (
        <>
          <FontAwesomeIcon icon={faPlay} className="govuk-!-margin-right-1" aria-hidden="true" />{' '}
          <a className="review-stat__link" href={link.href}>
            {link.label}
          </a>
        </>
      )}
    </div>
  );
}

const SERVICES_REQUIRING_ATTENTION = 'Total service codes that require attention';
const CONSUMER_INTERACTIONS = 'Total consumer interactions with your data';

interface ReviewBannerProps {
  kind: ReviewListKind;
  orgId: string;
  banner: ReviewListBanner;
}

export function ReviewBanner({ kind, orgId, banner }: ReviewBannerProps) {
  const dataActivityUrl = publishAppPath(
    `/org/${orgId}/dataset/data-activity?prev=${REVIEW_LIST_KINDS[kind].dataActivityPrev}`,
  );
  const attentionUrl = publishAppPath(`${reviewListPath(orgId, kind)}/attention`);

  if (kind === 'timetable') {
    const stats = banner as TimetableBanner;
    return (
      <>
        <ReviewStat
          top={stats.servicesRequiringAttention}
          bottom={`/${stats.applicableServices}`}
          description={SERVICES_REQUIRING_ATTENTION}
          link={{ href: attentionUrl, label: 'More details' }}
        />
        <ReviewStat
          top={stats.feedbackCount}
          description="Feedback messages received recently"
          link={{ href: dataActivityUrl, label: 'More details' }}
        />
        <ReviewStat
          top={stats.seasonalServicesCounter}
          description="Seasonal services"
          link={{
            href: publishAppPath(`/org/${orgId}/dataset/timetable/seasonal-service`),
            label: 'Manage',
          }}
        />
      </>
    );
  }

  if (kind === 'avl') {
    const stats = banner as AvlBanner;
    const hasScore = stats.overallPpcScore !== null && stats.overallPpcScore !== undefined;
    const matchingModal = (
      <b className="govuk-!-font-size-16 bods-relative-bottom">
        <AvlMatchingHelpModal />
      </b>
    );

    return (
      <>
        <ReviewStat
          top={stats.totalConsumerInteractions}
          description={CONSUMER_INTERACTIONS}
          link={{ href: dataActivityUrl, label: 'More details' }}
        />
        {hasScore ? (
          <ReviewStat
            top={
              <>
                {Math.round(stats.overallPpcScore as number)}%{' '}
                {matchingModal}
              </>
            }
            description="Weekly overall AVL to Timetables matching score"
            link={{
              href: publishAppPath(`/org/${orgId}/dataset/ppc-archive`),
              label: 'Download all archived matching reports',
            }}
          />
        ) : (
          <ReviewStat
            top={
              <>
                Pending {matchingModal}
              </>
            }
            description="Weekly overall AVL to Timetables matching score"
          />
        )}
        {stats.isAvlRequireAttentionActive && (
          <ReviewStat
            top={stats.servicesRequiringAttention}
            bottom={`/${stats.applicableServices}`}
            description={SERVICES_REQUIRING_ATTENTION}
            link={{ href: attentionUrl, label: 'More details' }}
          />
        )}
      </>
    );
  }

  const stats = banner as FaresBanner;
  if (stats.isFaresRequireAttentionActive) {
    return (
      <ReviewStat
        top={stats.servicesRequiringAttention}
        bottom={`/${stats.applicableServices}`}
        description={SERVICES_REQUIRING_ATTENTION}
        link={{ href: attentionUrl, label: 'More details' }}
      />
    );
  }

  return (
    <ReviewStat
      top={stats.totalConsumerInteractions}
      description={CONSUMER_INTERACTIONS}
      link={{ href: dataActivityUrl, label: 'More details' }}
    />
  );
}
