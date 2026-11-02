import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { api } from '@/lib/api-client';
import { publishAppPath } from '@/config/client';
import { FaresPublishSuccessPanel } from './FaresPublishSuccessPanel';

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '1', datasetId: '9' }),
}));

jest.mock('@/lib/api-client', () => ({
  api: { get: jest.fn() },
}));

const mockGet = api.get as jest.Mock;

describe('FaresPublishSuccessPanel', () => {
  beforeEach(() => jest.clearAllMocks());

  it('renders the published confirmation without calling the API', async () => {
    render(<FaresPublishSuccessPanel />);

    expect(
      await screen.findByRole('heading', { level: 1, name: 'Your data set has been successfully published' }),
    ).toBeInTheDocument();
    expect(mockGet).not.toHaveBeenCalled();
    expect(document.title).toBe('Data set published');
    expect(screen.getByRole('link', { name: 'your fares data sets' })).toHaveAttribute(
      'href',
      publishAppPath('/publish/org/1/dataset/fares'),
    );
  });

  describe('update', () => {
    it('renders the updated confirmation', async () => {
      mockGet.mockResolvedValue({ isFaresValidatorActive: true, validatorError: false });

      render(<FaresPublishSuccessPanel update />);

      expect(
        await screen.findByRole('heading', { level: 1, name: 'Your data set has been successfully updated' }),
      ).toBeInTheDocument();
      expect(mockGet).toHaveBeenCalledWith('/api/publish/fares/update-success/1/9/');
      expect(document.title).toBe('Data set updated');
      expect(screen.queryByText(/failed the validation set/)).not.toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'View published data set' })).toHaveAttribute(
        'href',
        publishAppPath('/publish/org/1/dataset/fares/9'),
      );
    });

    it('shows the validator paragraph when the live data failed validation', async () => {
      mockGet.mockResolvedValue({ isFaresValidatorActive: true, validatorError: true });

      render(<FaresPublishSuccessPanel update />);

      expect(
        await screen.findByText(
          'Your dataset failed the validation set and will be marked as not compliant. Please contact your supplier to create a compliant dataset.',
        ),
      ).toBeInTheDocument();
    });

    it('hides the validator paragraph when the flag is off', async () => {
      mockGet.mockResolvedValue({ isFaresValidatorActive: false, validatorError: true });

      render(<FaresPublishSuccessPanel update />);

      await screen.findByRole('heading', { level: 1 });
      expect(screen.queryByText(/failed the validation set/)).not.toBeInTheDocument();
    });

    it('shows an error when the context cannot be loaded', async () => {
      mockGet.mockRejectedValue(new Error('Dataset not found'));

      render(<FaresPublishSuccessPanel update />);

      expect(await screen.findByText('Dataset not found')).toBeInTheDocument();
    });
  });
});
