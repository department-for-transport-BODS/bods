import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ContactOperatorContent } from './ContactOperatorContent';
import { ContactOperatorSuccessContent } from './ContactOperatorSuccessContent';
import { ApiError, api } from '@/lib/api-client';
import { dataPath } from '@/config/client';

const mockPush = jest.fn();
const mockNotFound = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  notFound: () => mockNotFound(),
}));

jest.mock('@/lib/api-client', () => {
  class MockApiError extends Error {
    status: number;
    fieldErrors: Record<string, string[]>;
    constructor(message: string, status: number, fieldErrors: Record<string, string[]>) {
      super(message);
      this.status = status;
      this.fieldErrors = fieldErrors;
    }
    get hasFieldErrors() {
      return Object.keys(this.fieldErrors).length > 0;
    }
    firstFieldErrors() {
      return Object.fromEntries(Object.entries(this.fieldErrors).map(([key, messages]) => [key, messages[0]]));
    }
  }
  return { api: { get: jest.fn(), post: jest.fn() }, ApiError: MockApiError };
});

describe('ContactOperatorContent', () => {
  beforeEach(() => {
    jest.mocked(api.get).mockResolvedValue({ id: 12, name: 'Alpha Buses Limited' });
  });
  afterEach(() => jest.clearAllMocks());

  it('renders the Django heading, intro copy, fields and back link', async () => {
    render(<ContactOperatorContent operatorId="12" />);

    expect(await screen.findByRole('heading', { level: 1, name: 'Contact Alpha Buses Limited' })).toBeInTheDocument();
    expect(document.title).toBe('Provide feedback');
    expect(
      screen.getByText(
        'An email generated from this form will be sent to the data set/data feed owner directly. They will be your point of contact for any potential resolution to your query.',
      ),
    ).toBeInTheDocument();
    expect(screen.getByLabelText('What best describes the issue you are experiencing?*')).toBeInTheDocument();
    expect(screen.getByLabelText('Send this feedback anonymously')).not.toBeChecked();
    expect(screen.getByRole('button', { name: 'Send' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Back' })).toHaveAttribute('href', dataPath('/operators/12/'));
    expect(api.get).toHaveBeenCalledWith('/api/data/browser/operators/12/contact/');
  });

  it('shows Django’s required message in the summary and field, and prefixes the title', async () => {
    jest.mocked(api.post).mockRejectedValue(
      new ApiError('Validation failed', 400, { feedback: ['Enter feedback in the box below'] }),
    );
    render(<ContactOperatorContent operatorId="12" />);
    await screen.findByRole('heading', { level: 1 });

    await userEvent.click(screen.getByRole('button', { name: 'Send' }));

    expect(await screen.findByText('There is a problem')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Enter feedback in the box below' })).toHaveAttribute(
      'href',
      '#id_feedback',
    );
    expect(document.getElementById('feedback-error')).toHaveTextContent('Error: Enter feedback in the box below');
    expect(document.title).toBe('Error: Provide feedback');
    expect(mockPush).not.toHaveBeenCalled();
  });

  it('posts the feedback and redirects to the success page', async () => {
    jest.mocked(api.post).mockResolvedValue({ success: true });
    render(<ContactOperatorContent operatorId="12" />);
    await screen.findByRole('heading', { level: 1 });

    await userEvent.type(screen.getByLabelText(/What best describes/), 'Wrong stop times');
    await userEvent.click(screen.getByLabelText('Send this feedback anonymously'));
    await userEvent.click(screen.getByRole('button', { name: 'Send' }));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/api/data/browser/operators/12/contact/', {
        feedback: 'Wrong stop times',
        anonymous: true,
      }),
    );
    expect(mockPush).toHaveBeenCalledWith(dataPath('/operators/12/contact/success/'));
  });

  it('calls notFound() for an unknown operator', async () => {
    jest.mocked(api.get).mockRejectedValue(new ApiError('Operator not found', 404, {}));
    render(<ContactOperatorContent operatorId="999" />);
    await waitFor(() => expect(mockNotFound).toHaveBeenCalled());
  });
});

describe('ContactOperatorSuccessContent', () => {
  it('renders the confirmation, title and links back to the operators list', () => {
    render(<ContactOperatorSuccessContent />);

    expect(screen.getByRole('heading', { level: 1, name: 'Your feedback has been submitted' })).toBeInTheDocument();
    expect(document.title).toBe('Feedback sent');
    expect(screen.getByRole('button', { name: 'Go back to operators list' })).toHaveAttribute(
      'href',
      dataPath('/operators/'),
    );
    expect(screen.getByRole('link', { name: 'Back' })).toHaveAttribute('href', dataPath('/operators/'));
  });
});
