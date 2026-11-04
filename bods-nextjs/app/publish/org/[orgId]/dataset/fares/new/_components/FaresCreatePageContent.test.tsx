import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { publishAppPath, wwwPath } from '@/config/client';
import { api, ApiError } from '@/lib/api-client';
import { FaresCreatePageContent } from './FaresCreatePageContent';

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '7' }),
}));

jest.mock('@/lib/api-client', () => {
  const actual = jest.requireActual('@/lib/api-client');
  return { ...actual, api: { post: jest.fn() } };
});

const mockPost = api.post as jest.Mock;

function summaryLinks() {
  return Array.from(document.querySelectorAll('.govuk-error-summary__list a')).map((link) => [
    link.textContent,
    link.getAttribute('href'),
  ]);
}

function completeDescription() {
  fireEvent.change(screen.getByLabelText('Data set description'), { target: { value: 'Fares' } });
  fireEvent.change(screen.getByLabelText('Data set short description'), { target: { value: 'Short' } });
  fireEvent.click(screen.getByRole('button', { name: 'Continue' }));
}

describe('FaresCreatePageContent', () => {
  beforeEach(() => {
    mockPost.mockReset();
  });

  it('shows the Django description errors and links to the Django guidance and contact pages', () => {
    render(<FaresCreatePageContent />);
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }));

    expect(summaryLinks()).toEqual([
      ['Enter a description in the data set description box below', '#id_description-description'],
      ['Enter a short description in the data set short description box below', '#id_description-short_description'],
    ]);
    expect(document.title).toBe('Error: Publish new data set: description');
    expect(screen.getByRole('link', { name: 'View our guidelines here' })).toHaveAttribute(
      'href',
      publishAppPath('/guidance/operator-requirements'),
    );
    expect(screen.getByRole('link', { name: 'Contact support desk' })).toHaveAttribute(
      'href',
      wwwPath('/contact'),
    );
  });

  it.each([
    ['nothing selected', null, ['Please provide a file or url', '#id_url_link']],
    ['an empty link', 'Provide a link to your data set', ['Please provide a URL link', '#id_url_link']],
    ['no file', 'Upload data set to Bus Open Data Service', ['Please provide a file', '#id_upload_file']],
  ])('shows the Django upload error for %s', (_, radio, expected) => {
    render(<FaresCreatePageContent />);
    completeDescription();
    if (radio) {
      fireEvent.click(screen.getByLabelText(radio));
    }
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }));

    expect(summaryLinks()).toEqual([expected]);
    expect(document.querySelector('.govuk-error-message')).toHaveTextContent(expected[0] as string);
    expect(document.title).toBe('Error: Publish new data set: upload');
    expect(mockPost).not.toHaveBeenCalled();
  });

  it('shows Django field errors returned by the create API inline', async () => {
    mockPost.mockRejectedValue(
      new ApiError('Upload validation failed', 400, { url_link: ['Enter a valid URL to your data set'] }),
    );
    render(<FaresCreatePageContent />);
    completeDescription();
    fireEvent.click(screen.getByLabelText('Provide a link to your data set'));
    fireEvent.change(screen.getByLabelText('url link'), { target: { value: 'not a url' } });
    fireEvent.click(screen.getByRole('button', { name: 'Continue' }));

    await waitFor(() =>
      expect(summaryLinks()).toEqual([['Enter a valid URL to your data set', '#id_url_link']]),
    );
    expect(screen.getByLabelText('url link')).toHaveClass('govuk-input--error');
  });

  it('renders the Django cancel step and returns to the previous step', () => {
    render(<FaresCreatePageContent />);
    completeDescription();
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(
      screen.getByRole('heading', { level: 1, name: 'Would you like to cancel publishing this data set?' }),
    ).toHaveClass('govuk-heading-xl');
    expect(screen.getByRole('button', { name: 'Confirm' })).toHaveAttribute(
      'href',
      publishAppPath('/org/7/dataset/fares'),
    );
    expect(document.title).toBe('Publish new data set: cancel');
    expect(screen.queryByText('Need help with operator data requirements?')).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Back' }));
    expect(screen.getByRole('heading', { level: 1, name: 'Choose how to provide your data set' })).toBeInTheDocument();
  });
});
