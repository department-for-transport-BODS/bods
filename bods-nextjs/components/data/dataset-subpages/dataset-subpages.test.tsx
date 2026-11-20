import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { ApiError, api } from '@/lib/api-client';
import { ChangelogPageContent } from './ChangelogPageContent';
import { FeedbackPageContent, FeedbackSuccessPageContent } from './FeedbackPageContent';
import { SubscriptionPageContent, SubscriptionSuccessPageContent } from './SubscriptionPageContent';
import type { DatasetChangelog, DatasetFeedback, DatasetSubscriptionState } from './types';

const mockPush = jest.fn();
let mockSearch = '';

class MockNotFound extends Error {}

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), refresh: jest.fn() }),
  useParams: () => ({ id: '7' }),
  useSearchParams: () => new URLSearchParams(mockSearch),
  usePathname: () => '/',
  notFound: () => {
    throw new MockNotFound('NEXT_NOT_FOUND');
  },
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => {
  const actual = jest.requireActual('@/lib/api-client');
  return { ...actual, api: { get: jest.fn(), post: jest.fn() } };
});

const mockGet = api.get as jest.Mock;
const mockPost = api.post as jest.Mock;

function changelog(overrides: Partial<DatasetChangelog> = {}): DatasetChangelog {
  return {
    datasetId: 7,
    datasetType: 'TIMETABLE',
    name: 'My dataset',
    showDataQuality: true,
    count: 2,
    page: 1,
    pageSize: 10,
    totalPages: 1,
    results: [
      {
        revisionId: 1,
        comment: 'First upload',
        statusLabel: 'Published',
        statusClass: 'status-indicator--success',
        updatedAt: '1 January 2024',
        showErrors: false,
        errors: [],
        dataQuality: { score: '90%', ragLevel: 'Green', indicator: 'success' },
      },
      {
        revisionId: 2,
        comment: 'Second upload',
        statusLabel: 'Error',
        statusClass: 'status-indicator--error',
        updatedAt: '2 January 2024',
        showErrors: true,
        errors: ['Bad file', 'Worse file'],
        dataQuality: { text: 'Not available' },
      },
    ],
    ...overrides,
  };
}

function subscription(overrides: Partial<DatasetSubscriptionState> = {}): DatasetSubscriptionState {
  return {
    datasetId: 7,
    datasetType: 'TIMETABLE',
    name: 'My dataset',
    detailPath: '/timetable/dataset/7/detail',
    isAuthenticated: true,
    isSubscribed: false,
    ...overrides,
  };
}

function feedback(overrides: Partial<DatasetFeedback> = {}): DatasetFeedback {
  return {
    datasetId: 7,
    datasetType: 'TIMETABLE',
    name: 'My dataset',
    service: null,
    lineName: null,
    stopName: null,
    atcoCode: null,
    journeyStartTime: null,
    direction: null,
    backPath: '/timetable/dataset/7/detail',
    ...overrides,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  mockSearch = '';
});

describe('ChangelogPageContent', () => {
  it('renders the table with data quality and error rows', async () => {
    mockGet.mockResolvedValue(changelog());
    render(<ChangelogPageContent kind="timetables" />);

    expect(await screen.findByRole('heading', { level: 1, name: 'My dataset' })).toBeInTheDocument();
    expect(mockGet).toHaveBeenCalledWith('/api/data/browser/timetables/7/changelog/');
    expect(screen.getByRole('columnheader', { name: 'Data quality' })).toBeInTheDocument();
    expect(screen.getByText('Green')).toHaveClass('status-indicator--success');
    expect(screen.getByText('Not available')).toBeInTheDocument();
    expect(screen.getByText('Bad file')).toBeInTheDocument();
    expect(screen.getByText('Worse file').closest('td')).toHaveAttribute('colspan', '4');
    expect(screen.getByRole('link', { name: 'Back' })).toHaveAttribute('href', '/timetable/dataset/7');
    expect(document.title).toBe('Changelog');
  });

  it('omits the data quality column for AVL and passes the page number on', async () => {
    mockSearch = 'page=2';
    mockGet.mockResolvedValue(changelog({ showDataQuality: false, page: 2, totalPages: 3 }));
    render(<ChangelogPageContent kind="avl" />);

    await screen.findByRole('heading', { level: 1 });
    expect(mockGet).toHaveBeenCalledWith('/api/data/browser/avl/7/changelog/?page=2');
    expect(screen.queryByRole('columnheader', { name: 'Data quality' })).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Back' })).toHaveAttribute('href', '/avl/dataset/7');
  });

  it('shows an error summary when the changelog cannot be loaded', async () => {
    mockGet.mockRejectedValue(new Error('boom'));
    render(<ChangelogPageContent kind="fares" />);

    expect(await screen.findByText('Unable to load the changelog. Please refresh and try again.')).toBeInTheDocument();
  });

  it('renders the not-found page when Django answers 404', async () => {
    mockGet.mockRejectedValue(new ApiError('Not found', 404, {}));
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => undefined);

    // notFound() throws during render; React reports it to the nearest boundary.
    class Boundary extends (await import('react')).Component<{ children: React.ReactNode }, { failed: boolean }> {
      state = { failed: false };
      static getDerivedStateFromError() {
        return { failed: true };
      }
      render() {
        return this.state.failed ? <p>not found boundary</p> : this.props.children;
      }
    }

    render(
      <Boundary>
        <ChangelogPageContent kind="timetables" />
      </Boundary>,
    );

    expect(await screen.findByText('not found boundary')).toBeInTheDocument();
    consoleError.mockRestore();
  });
});

describe('SubscriptionPageContent', () => {
  it('asks to subscribe and posts, then moves to the success page', async () => {
    mockGet.mockResolvedValue(subscription());
    mockPost.mockResolvedValue({});
    render(<SubscriptionPageContent kind="timetables" />);

    expect(await screen.findByRole('heading', { level: 1, name: 'Subscribe to data set' })).toBeInTheDocument();
    expect(screen.getByText('Would you like to subscribe to My dataset data set?')).toBeInTheDocument();
    expect(document.title).toBe('Subscribe to data set');

    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }));

    await waitFor(() => expect(mockPush).toHaveBeenCalledWith('/timetable/dataset/7/subscription/success'));
    expect(mockPost).toHaveBeenCalledWith('/api/data/browser/timetables/7/subscription/', {});
  });

  it('asks to unsubscribe from an AVL data feed', async () => {
    mockGet.mockResolvedValue(subscription({ datasetType: 'AVL', isSubscribed: true }));
    render(<SubscriptionPageContent kind="avl" />);

    expect(await screen.findByRole('heading', { level: 1, name: 'Unsubscribe from data feed' })).toBeInTheDocument();
    expect(screen.getByText('Would you like to unsubscribe from My dataset data feed?')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Cancel' })).toHaveAttribute('href', '/avl/dataset/7');
  });

  it('shows the sign-in gatekeeper to anonymous visitors', async () => {
    mockGet.mockResolvedValue(subscription({ isAuthenticated: false, isSubscribed: null }));
    render(<SubscriptionPageContent kind="fares" />);

    expect(await screen.findByRole('heading', { name: 'Get data set updates' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Sign in' })).toHaveAttribute('href', '/account/login/');
    expect(screen.getByRole('link', { name: 'Create account' })).toHaveAttribute('href', '/account/signup/');
    expect(mockPost).not.toHaveBeenCalled();
  });

  it('shows an error summary when the post fails', async () => {
    mockGet.mockResolvedValue(subscription());
    mockPost.mockRejectedValue(new Error('nope'));
    render(<SubscriptionPageContent kind="timetables" />);

    fireEvent.click(await screen.findByRole('button', { name: 'Confirm' }));

    expect(await screen.findByRole('alert')).toBeInTheDocument();
    expect(mockPush).not.toHaveBeenCalled();
  });
});

describe('SubscriptionSuccessPageContent', () => {
  it('confirms a subscription', async () => {
    mockGet.mockResolvedValue(
      subscription({ isSubscribed: true, backPath: '/account/manage?page=2', backButtonText: 'Go back to manage subscriptions' }),
    );
    render(<SubscriptionSuccessPageContent kind="timetables" />);

    expect(
      await screen.findByRole('heading', { name: 'You have successfully subscribed to the data set' }),
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Go back to manage subscriptions' })).toHaveAttribute(
      'href',
      '/account/manage?page=2',
    );
    expect(screen.queryByRole('link', { name: 'Back' })).not.toBeInTheDocument();
    expect(document.title).toBe('Subscribed successfully');
  });

  it('confirms an unsubscription from an AVL feed', async () => {
    mockGet.mockResolvedValue(
      subscription({ datasetType: 'AVL', isSubscribed: false, backPath: '/avl/dataset/7', backButtonText: 'Go back to data feed' }),
    );
    render(<SubscriptionSuccessPageContent kind="avl" />);

    expect(
      await screen.findByRole('heading', { name: 'You will no longer receive notification on the data feed' }),
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Go back to data feed' })).toBeInTheDocument();
    expect(document.title).toBe('Unsubscribed successfully');
  });
});

describe('FeedbackPageContent', () => {
  it('renders the form with the dataset details and the optional rows', async () => {
    mockSearch = 'service=Svc&line=12';
    mockGet.mockResolvedValue(
      feedback({
        service: 'Svc',
        lineName: '12',
        stopName: 'High St',
        atcoCode: '0100X',
        journeyStartTime: '10:00',
        direction: 'outbound',
      }),
    );
    render(<FeedbackPageContent kind="timetables" />);

    expect(await screen.findByRole('heading', { name: 'Contact the data set owner' })).toBeInTheDocument();
    expect(mockGet).toHaveBeenCalledWith('/api/data/browser/timetables/7/feedback/?service=Svc&line=12');
    expect(screen.getByText('Data set ID')).toBeInTheDocument();
    expect(screen.getByText('12 - Svc')).toBeInTheDocument();
    expect(screen.getByText('High St - 0100X')).toBeInTheDocument();
    expect(screen.getByText('10:00')).toBeInTheDocument();
    expect(screen.getByText('outbound')).toBeInTheDocument();
    expect(screen.getByLabelText('What best describes the issue you are experiencing?*')).toBeInTheDocument();
    expect(screen.getByLabelText('Send this feedback anonymously')).not.toBeChecked();
  });

  it('uses "data feed" wording for AVL datasets', async () => {
    mockGet.mockResolvedValue(feedback({ datasetType: 'AVL' }));
    render(<FeedbackPageContent kind="avl" />);

    expect(await screen.findByRole('heading', { name: 'Contact the data feed owner' })).toBeInTheDocument();
    expect(screen.getByText('Data feed ID')).toBeInTheDocument();
  });

  it('shows Django field errors in the summary and beside the field', async () => {
    mockGet.mockResolvedValue(feedback());
    mockPost.mockRejectedValue(new ApiError('Invalid', 400, { feedback: ['Please provide feedback.'] }));
    render(<FeedbackPageContent kind="timetables" />);

    fireEvent.click(await screen.findByRole('button', { name: 'Send' }));

    const message = await screen.findByText('Please provide feedback.', { selector: '.govuk-error-message' });
    expect(message).toHaveAttribute('id', '1_id_feedback-error');
    expect(screen.getByRole('link', { name: 'Please provide feedback.' })).toHaveAttribute('href', '#id_feedback');
    expect(document.title).toBe('Error: Provide feedback');
    expect(mockPush).not.toHaveBeenCalled();
  });

  it('posts the feedback and follows the redirect path', async () => {
    mockSearch = 'service=Svc';
    mockGet.mockResolvedValue(feedback());
    mockPost.mockResolvedValue({ redirectPath: '/timetable/dataset/7/feedback/success?service=Svc' });
    render(<FeedbackPageContent kind="timetables" />);

    fireEvent.change(await screen.findByLabelText('What best describes the issue you are experiencing?*'), {
      target: { value: 'Wrong times' },
    });
    fireEvent.click(screen.getByLabelText('Send this feedback anonymously'));
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Send' }));
    });

    expect(mockPost).toHaveBeenCalledWith('/api/data/browser/timetables/7/feedback/?service=Svc', {
      feedback: 'Wrong times',
      anonymous: true,
    });
    expect(mockPush).toHaveBeenCalledWith('/timetable/dataset/7/feedback/success?service=Svc');
  });
});

describe('FeedbackSuccessPageContent', () => {
  it('thanks the user and links back', async () => {
    mockGet.mockResolvedValue({ backPath: '/timetable/dataset/7/detail' });
    render(<FeedbackSuccessPageContent kind="timetables" />);

    expect(await screen.findByRole('heading', { name: 'Your feedback has been submitted' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Go back to data set' })).toHaveAttribute(
      'href',
      '/timetable/dataset/7/detail',
    );
    expect(screen.getByRole('link', { name: 'Back' })).toHaveAttribute('href', '/timetable/dataset/7/detail');
    expect(document.title).toBe('Feedback sent');
  });
});
