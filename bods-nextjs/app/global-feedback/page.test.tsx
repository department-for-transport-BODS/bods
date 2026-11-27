import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import FeedbackPage from './page';
import { FeedbackForm } from './_components/FeedbackForm';

const mockPush = jest.fn();
const mockPost = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock('@/lib/api-client', () => ({
  ...jest.requireActual('@/lib/api-client'),
  api: { post: (...args: unknown[]) => mockPost(...args) },
}));

describe('FeedbackForm', () => {
  beforeEach(() => {
    mockPush.mockReset();
    mockPost.mockReset();
  });

  it('posts the originating url and goes to the global-feedback thank-you page', async () => {
    mockPost.mockResolvedValue({});
    render(<FeedbackForm pageUrl="www.example.com/changelog" />);

    fireEvent.click(screen.getByRole('button', { name: 'Send Feedback' }));

    await waitFor(() => expect(mockPush).toHaveBeenCalledWith('/global-feedback/thank-you/'));
    expect(mockPost).toHaveBeenCalledWith('/api/www/feedback/', {
      satisfaction_rating: 2,
      comment: '',
      page_url: 'www.example.com/changelog',
    });
  });

  it('prefills the hidden page_url from the ?url= query parameter', async () => {
    render(
      await FeedbackPage({
        searchParams: Promise.resolve({ url: 'www.example.com/changelog' }),
      }),
    );

    expect(screen.getByDisplayValue('www.example.com/changelog')).toHaveAttribute(
      'name',
      'page_url',
    );
  });
  it('renders Django-equivalent rating, comment limit, and originating URL', () => {
    render(<FeedbackForm pageUrl="https://www.example.com/changelog" />);

    expect(screen.getByRole('heading', { name: 'Give feedback on Bus Open Data Service' })).toHaveClass(
      'govuk-heading-xl',
    );
    expect(screen.getByText('Satisfaction Rating')).toHaveClass('govuk-fieldset__legend--xl');
    expect(screen.getByRole('group', { name: 'Satisfaction Rating' })).toBeInTheDocument();
    expect(screen.getByLabelText('Comment')).toHaveAttribute('name', 'comment');
    expect(screen.getByText(/You have 1200/)).toHaveClass('govuk-hint');
    expect(screen.getByRole('radio', { name: 'Satisfied' })).toBeChecked();
    expect(screen.getByText('How did you find Bus Open Data Service today?')).toBeInTheDocument();
    expect(screen.getByText('How could we improve this service? (optional)')).toBeInTheDocument();
    expect(screen.getByLabelText('Comment')).toHaveAttribute(
      'maxLength',
      '1200',
    );
    expect(screen.getByDisplayValue('https://www.example.com/changelog')).toHaveAttribute(
      'name',
      'page_url',
    );
  });

  it('renders the Twitter link with its icon in the sidebar', async () => {
    render(await FeedbackPage({ searchParams: Promise.resolve({}) }));

    const link = screen.getByRole('link', { name: /Bus open data service Twitter/ });
    expect(link).toHaveAttribute('href', 'https://twitter.com/busopendata?ref_src=twsrc%5Etfw');
    expect(screen.getByAltText('twitter icon')).toHaveAttribute('src', '/assets/images/feedback/twitter_icon.png');
  });
});
