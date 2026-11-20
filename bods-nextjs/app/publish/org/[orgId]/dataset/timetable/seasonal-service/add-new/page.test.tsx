import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SeasonalServiceAddNewPage from './page';
import { ApiError, api } from '@/lib/api-client';

const mockPush = jest.fn();
let mockSearch = '';

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '55' }),
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => new URLSearchParams(mockSearch),
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => ({
  ...jest.requireActual('@/lib/api-client'),
  api: { get: jest.fn(), post: jest.fn() },
}));

const validationError = (fieldErrors: Record<string, string[]>) =>
  new ApiError('Validation failed', 400, fieldErrors);

const goToStepTwo = async () => {
  await userEvent.selectOptions(await screen.findByLabelText('PSV licence number'), '2');
  await userEvent.click(screen.getByRole('button', { name: 'Continue' }));
  await screen.findByLabelText('Service code');
};

describe('Seasonal services - add new wizard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearch = '';
    (api.get as jest.Mock).mockResolvedValue({
      organisationId: 55,
      organisationName: 'ZZ Org',
      isAgentUser: false,
      licences: [
        { id: 2, number: 'ZZ0000001' },
        { id: 3, number: 'ZZ0000002' },
      ],
    });
    (api.post as jest.Mock).mockImplementation((path: string) =>
      Promise.resolve(path.endsWith('validate-licence/') ? { licence: { id: 2, number: 'ZZ0000001' } } : { id: 9 }),
    );
  });

  it('renders step 1 with the stepper, guidance and licence options', async () => {
    render(<SeasonalServiceAddNewPage />);

    expect(await screen.findByRole('heading', { level: 1, name: 'Seasonal service operating dates' })).toBeInTheDocument();
    expect(screen.getByText('Select the PSV licence number to add seasonal service operating dates.')).toBeInTheDocument();
    expect(screen.getByText('1. Select PSV licence number')).toHaveClass('publish-stepper__item--selected');
    expect(screen.getByText('2. Provide operating dates')).toHaveClass('publish-stepper__item--next');
    expect(screen.getByRole('option', { name: 'Select PSV licence number' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'ZZ0000002' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Add new' })).toBeInTheDocument();
  });

  it('shows the Django validation error when no licence is selected', async () => {
    (api.post as jest.Mock).mockRejectedValue(validationError({ licence: ['This field is required.'] }));
    render(<SeasonalServiceAddNewPage />);

    await userEvent.click(await screen.findByRole('button', { name: 'Continue' }));

    expect(await screen.findByRole('heading', { name: 'There is a problem' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'This field is required.' })).toHaveAttribute(
      'href',
      '#id_select_psv_licence_number-licence',
    );
    expect(document.title).toBe('Error: Bus Open Data Service');
    expect(api.post).toHaveBeenCalledWith('/api/publish/seasonal-services/55/validate-licence/', { licence: '' });
  });

  it('moves to step 2 after the licence is validated and shows the licence', async () => {
    render(<SeasonalServiceAddNewPage />);

    await goToStepTwo();

    expect(api.post).toHaveBeenCalledWith('/api/publish/seasonal-services/55/validate-licence/', { licence: '2' });
    expect(screen.getByText('PSV Licence Number')).toBeInTheDocument();
    expect(screen.getByText('ZZ0000001/')).toBeInTheDocument();
    expect(screen.getByText('1. Select PSV licence number')).toHaveClass('publish-stepper__item--previous');
    expect(screen.getByLabelText('Service begins on')).toHaveAttribute('type', 'date');
    expect(screen.getByLabelText('Service ends on')).toHaveAttribute('type', 'date');
    expect(screen.queryByText('Select the PSV licence number to add seasonal service operating dates.')).not.toBeInTheDocument();
  });

  it('shows the help modal text for the operating dates', async () => {
    render(<SeasonalServiceAddNewPage />);
    await goToStepTwo();

    await userEvent.click(screen.getByRole('button', { name: 'Help' }));

    expect(screen.getByText('Use the date range to mark when this service intends to operate.')).toBeInTheDocument();
    expect(screen.getByText(/mark the date the service starts for the Christmas period/)).toBeInTheDocument();
  });

  it('maps step 2 field errors onto the fields and the error summary', async () => {
    render(<SeasonalServiceAddNewPage />);
    await goToStepTwo();
    (api.post as jest.Mock).mockRejectedValue(
      validationError({
        registrationCode: ['Enter a service code in the box below'],
        end: ['Start date must be earlier than end date'],
      }),
    );

    await userEvent.click(screen.getByRole('button', { name: 'Save' }));

    const codeLink = await screen.findByRole('link', { name: 'Enter a service code in the box below' });
    expect(codeLink).toHaveAttribute('href', '#id_provide_operating_dates-registration_code');
    expect(screen.getByRole('link', { name: 'Start date must be earlier than end date' })).toHaveAttribute(
      'href',
      '#id_provide_operating_dates-end',
    );
    expect(document.getElementById('1_id_provide_operating_dates-registration_code-error')).toHaveTextContent(
      'Enter a service code in the box below',
    );
    expect(document.getElementById('1_id_provide_operating_dates-end-error')).toBeInTheDocument();
    expect(document.getElementById('1_id_provide_operating_dates-start-error')).not.toBeInTheDocument();
  });

  it('creates the service and returns to the list keeping the page', async () => {
    mockSearch = 'page=2';
    render(<SeasonalServiceAddNewPage />);
    await goToStepTwo();

    await userEvent.type(screen.getByLabelText('Service code'), '123');
    await userEvent.type(screen.getByLabelText('Service begins on'), '2030-05-01');
    await userEvent.type(screen.getByLabelText('Service ends on'), '2030-06-01');
    await userEvent.click(screen.getByRole('button', { name: 'Save' }));

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/api/publish/seasonal-services/55/create/', {
        licence: '2',
        registrationCode: '123',
        start: '2030-05-01',
        end: '2030-06-01',
      }),
    );
    await waitFor(() =>
      expect(mockPush).toHaveBeenCalledWith(
        expect.stringContaining('/org/55/dataset/timetable/seasonal-service/?page=2&'),
      ),
    );
  });

  it('restarts from step 1 when Edit is chosen on step 2', async () => {
    render(<SeasonalServiceAddNewPage />);
    await goToStepTwo();

    await userEvent.click(screen.getByRole('link', { name: 'Edit' }));

    expect(await screen.findByLabelText('PSV licence number')).toHaveValue('');
    expect(screen.getByText('1. Select PSV licence number')).toHaveClass('publish-stepper__item--selected');
  });
});
