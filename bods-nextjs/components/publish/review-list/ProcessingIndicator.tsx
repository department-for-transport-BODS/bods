'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api-client';

/** Django's feed-list-progress.js polls every 10 seconds. */
export const PROCESSING_POLL_INTERVAL_MS = 10000;

const PIE_SIZE = 18;
const PIE_CENTRE = PIE_SIZE / 2;
const PIE_STROKE_WIDTH = 9;
const PIE_RADIUS = PIE_CENTRE - PIE_STROKE_WIDTH / 2;

interface ProgressResponse {
  progress: number;
  status: string;
}

type Phase =
  | { kind: 'processing'; progress: number | null }
  | { kind: 'draft' }
  | { kind: 'error' }
  | { kind: 'unknown' };

const TERMINAL_INDICATORS = {
  draft: { className: 'status-indicator--draft', title: 'Draft' },
  error: { className: 'status-indicator--error', title: 'Error' },
  // Django's UNKNOWN fallback: still labelled "Processing" but styled as success.
  unknown: { className: 'status-indicator--success', title: 'Processing' },
} as const;

/** Port of describeArc() from transit_odp/frontend/assets/js/bods-maths.js. */
export function describeArc(x: number, y: number, radius: number, startAngle: number, endAngle: number): string {
  const polar = (angle: number) => {
    const radians = ((angle - 90) * Math.PI) / 180;
    return { x: x + radius * Math.cos(radians), y: y + radius * Math.sin(radians) };
  };
  const start = polar(endAngle);
  const end = polar(startAngle);
  const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';
  return ['M', start.x, start.y, 'A', radius, radius, 0, largeArcFlag, 0, end.x, end.y].join(' ');
}

function phaseFor({ progress, status }: ProgressResponse): Phase {
  // Mirrors Dataset.queryAPI() in feed-list-progress.js.
  if (status === 'indexing' && progress < 100) return { kind: 'processing', progress };
  if (status === 'success') return { kind: 'draft' };
  if (status === 'error') return { kind: 'error' };
  return { kind: 'unknown' };
}

interface ProcessingIndicatorProps {
  datasetId: number;
  /** href of the "View" link Django appends once processing ends; null on the non-active tabs. */
  viewHref: string | null;
}

/**
 * Port of the `.progress-centre` pie indicator plus the polling in feed-list-progress.js:
 * GET /dataset/<id>/progress/ immediately and then every 10s, updating the pie while the
 * revision is indexing, and swapping to Draft / Error / Processing (success style) and
 * stopping as soon as it is anything else (or the request fails).
 */
export function ProcessingIndicator({ datasetId, viewHref }: ProcessingIndicatorProps) {
  const [phase, setPhase] = useState<Phase>({ kind: 'processing', progress: null });

  useEffect(() => {
    let cancelled = false;
    let intervalId: ReturnType<typeof setInterval> | undefined;

    const stop = () => {
      if (intervalId !== undefined) clearInterval(intervalId);
      intervalId = undefined;
    };

    const poll = async () => {
      let next: Phase;
      try {
        next = phaseFor(await api.get<ProgressResponse>(`/api/publish/dataset/${datasetId}/progress/`));
      } catch (error) {
        console.error(`Cannot contact API, giving up: ${error}`);
        next = { kind: 'unknown' };
      }
      if (cancelled) return;
      setPhase(next);
      if (next.kind !== 'processing') stop();
    };

    void poll();
    intervalId = setInterval(() => void poll(), PROCESSING_POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      stop();
    };
  }, [datasetId]);

  if (phase.kind === 'processing') {
    const progress = phase.progress;
    return (
      <div className="progress-centre">
        <div id={String(datasetId)} className="pie-progress">
          <svg width={PIE_SIZE} height={PIE_SIZE}>
            <circle r="9" cx="9" cy="9" stroke="none" strokeWidth="0" fill="#7fb19a"></circle>
            <path
              fill="none"
              stroke="#006435"
              strokeWidth={PIE_STROKE_WIDTH}
              strokeLinecap="butt"
              d={
                progress === null
                  ? undefined
                  : describeArc(PIE_CENTRE, PIE_CENTRE, PIE_RADIUS, 0, (360 / 100) * (progress + 1))
              }
            ></path>
          </svg>
          <span className="progress-percent">{progress === null ? '' : `${progress}%`}</span>
          <span className="progress-text">Processing</span>
        </div>
      </div>
    );
  }

  const { className, title } = TERMINAL_INDICATORS[phase.kind];
  return (
    <>
      <span className={`status-indicator ${className}`}>{title}</span>
      {viewHref && (
        <>
          {' '}
          <a className="govuk-link govuk-!-padding-left-1" href={viewHref}>
            View
          </a>
        </>
      )}
    </>
  );
}
