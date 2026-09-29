import { act, renderHook } from '@testing-library/react';
import { REVIEW_POLL_INTERVAL_MS, useDatasetReview } from './useDatasetReview';

const mockApiGet = jest.fn();

jest.mock('@/lib/api-client', () => ({
  api: {
    get: (...args: unknown[]) => mockApiGet(...args),
  },
}));

type Review = {
  loading: boolean;
  progress: number;
  dqStatus?: string;
};

const REVIEW_PATH = '/api/publish/timetables/review-status/1/2/';
const PROGRESS_PATH = '/api/publish/dataset/2/progress/';

const callsTo = (path: string) => mockApiGet.mock.calls.filter(([p]) => p === path).length;

function mockResponses(reviews: Review[], progress = { progress: 100, status: 'success' }) {
  let reviewIndex = 0;
  mockApiGet.mockImplementation((path: string) => {
    if (path === PROGRESS_PATH) return Promise.resolve(progress);
    const review = reviews[Math.min(reviewIndex, reviews.length - 1)];
    reviewIndex += 1;
    return Promise.resolve(review);
  });
}

async function flush(ms = 0) {
  await act(async () => {
    await jest.advanceTimersByTimeAsync(ms);
  });
}

describe('useDatasetReview', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('renders straight from the review status without progress polling when already processed', async () => {
    mockResponses([{ loading: false, progress: 100 }]);

    const { result } = renderHook(() =>
      useDatasetReview<Review>('2', REVIEW_PATH, undefined, '', { fetchReviewFirst: true }),
    );
    await flush();
    await flush(5000);

    expect(result.current.isInitialLoading).toBe(false);
    expect(result.current.statusData?.loading).toBe(false);
    expect(callsTo(PROGRESS_PATH)).toBe(0);
    expect(callsTo(REVIEW_PATH)).toBe(1);
  });

  it('keeps polling when progress is 100 but the review is still loading', async () => {
    mockResponses([
      { loading: true, progress: 0 },
      { loading: true, progress: 100 },
      { loading: false, progress: 100 },
    ]);

    const { result } = renderHook(() =>
      useDatasetReview<Review>('2', REVIEW_PATH, undefined, '', { fetchReviewFirst: true }),
    );
    await flush();
    expect(result.current.statusData?.loading).toBe(true);

    await flush(1000);
    await flush(1000);
    expect(result.current.statusData?.loading).toBe(false);

    const progressCalls = callsTo(PROGRESS_PATH);
    await flush(5000);
    expect(callsTo(PROGRESS_PATH)).toBe(progressCalls);
  });

  it('re-fetches the review while keepPollingReview is true, then stops', async () => {
    mockResponses([
      { loading: false, progress: 100, dqStatus: 'PENDING' },
      { loading: false, progress: 100, dqStatus: 'PENDING' },
      { loading: false, progress: 100, dqStatus: 'SUCCESS' },
    ]);

    const { result } = renderHook(() =>
      useDatasetReview<Review>('2', REVIEW_PATH, undefined, '', {
        fetchReviewFirst: true,
        keepPollingReview: (data) => data.dqStatus === 'PENDING',
      }),
    );
    await flush();
    expect(result.current.statusData?.dqStatus).toBe('PENDING');

    await flush(REVIEW_POLL_INTERVAL_MS);
    expect(result.current.statusData?.dqStatus).toBe('PENDING');

    await flush(REVIEW_POLL_INTERVAL_MS);
    expect(result.current.statusData?.dqStatus).toBe('SUCCESS');

    await flush(REVIEW_POLL_INTERVAL_MS * 3);
    expect(callsTo(REVIEW_PATH)).toBe(3);
  });

  it('polls progress before fetching the review by default', async () => {
    mockResponses([{ loading: false, progress: 100 }]);

    const { result } = renderHook(() => useDatasetReview<Review>('2', REVIEW_PATH));
    await flush();

    expect(mockApiGet.mock.calls[0][0]).toBe(PROGRESS_PATH);
    expect(result.current.statusData?.loading).toBe(false);
  });
});
