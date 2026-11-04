import { render, screen } from '@testing-library/react';
import { FeedbackForm } from './_components/FeedbackForm';

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn() }),
}));

describe('FeedbackForm', () => {
  it('renders Django-equivalent rating, comment limit, and originating URL', () => {
    render(<FeedbackForm pageUrl="https://www.example.com/changelog" />);

    expect(screen.getByRole('heading', { name: 'Give feedback on Bus Open Data Service' })).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'Satisfied' })).toBeChecked();
    expect(screen.getByLabelText('How could we improve this service? (optional)')).toHaveAttribute(
      'maxLength',
      '1200',
    );
    expect(screen.getByDisplayValue('https://www.example.com/changelog')).toHaveAttribute(
      'name',
      'page_url',
    );
  });
});
