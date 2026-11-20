import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import '@testing-library/jest-dom';
import { publishPath } from '@/config/client';
import { ApiError, api } from '@/lib/api-client';
import { EDIT_DESCRIPTION_ERRORS } from '@/lib/validation/messages';
import { EditDescriptionContent } from './EditDescriptionContent';

const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '1', datasetId: '9' }),
  useRouter: () => ({ push: mockPush }),
}));

jest.mock('@/lib/api-client', () => {
  const actual = jest.requireActual('@/lib/api-client');
  return { ...actual, api: { get: jest.fn(), post: jest.fn() } };
});

const mockGet = api.get as jest.Mock;
const mockPost = api.post as jest.Mock;

const context = {
  datasetId: 9,
  name: 'A very long data set revision name',
  description: 'Current description',
  shortDescription: 'Current short',
  isRevisionUpdate: false,
};

async function renderPage(
  props: Parameters<typeof EditDescriptionContent>[0],
  response: Partial<typeof context> = {},
) {
  mockGet.mockResolvedValue({ ...context, ...response });
  render(<EditDescriptionContent {...props} />);
  await screen.findByRole('heading', { level: 1, name: 'Edit description' });
}

function breadcrumbLink(name: string) {
  return within(screen.getByRole('navigation', { name: 'Breadcrumb' })).getByRole('link', { name });
}

describe('EditDescriptionContent', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it.each([
    ['timetable', 'live', '/api/publish/timetables/dataset-edit/1/9/'],
    ['timetable', 'draft', '/api/publish/timetables/revision-edit/1/9/'],
    ['fares', 'live', '/api/publish/fares/dataset-edit/1/9/'],
    ['fares', 'draft', '/api/publish/fares/revision-edit/1/9/'],
  ] as const)('loads the %s %s revision and pre-fills the form', async (datasetType, mode, apiUrl) => {
    await renderPage({ datasetType, mode });

    expect(mockGet).toHaveBeenCalledWith(apiUrl);
    expect(screen.getByLabelText('Data set description')).toHaveValue('Current description');
    expect(screen.getByLabelText('Data set short description')).toHaveValue('Current short');
    expect(screen.getByLabelText('Data set short description')).toHaveAttribute('maxlength', '30');
    expect(breadcrumbLink('Your data sets')).toHaveAttribute(
      'href',
      publishPath(`/org/1/dataset/${datasetType}/`),
    );
    expect(breadcrumbLink('Edit description')).toHaveAttribute(
      'href',
      publishPath(`/org/1/dataset/${datasetType}/9/dataset-edit/`),
    );
  });

  it.each([
    ['live', false, '/org/1/dataset/fares/9/'],
    ['draft', false, '/org/1/dataset/fares/9/review/'],
    ['draft', true, '/org/1/dataset/fares/9/update/review/'],
  ] as const)(
    'links the truncated name and cancel to the %s return page (update: %s)',
    async (mode, isRevisionUpdate, returnPath) => {
      await renderPage({ datasetType: 'fares', mode }, { isRevisionUpdate });

      expect(breadcrumbLink('A very long data se...')).toHaveAttribute('href', publishPath(returnPath));

      fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

      expect(mockPush).toHaveBeenCalledWith(publishPath(returnPath));
      expect(mockPost).not.toHaveBeenCalled();
    },
  );

  it('saves the description and returns to the review page', async () => {
    mockPost.mockResolvedValue(context);
    await renderPage({ datasetType: 'timetable', mode: 'draft' }, { isRevisionUpdate: true });

    fireEvent.change(screen.getByLabelText('Data set description'), {
      target: { value: 'New description' },
    });
    fireEvent.change(screen.getByLabelText('Data set short description'), {
      target: { value: 'New short' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Save and continue' }));

    await waitFor(() =>
      expect(mockPush).toHaveBeenCalledWith(publishPath('/org/1/dataset/timetable/9/update/review/')),
    );
    const [url, body] = mockPost.mock.calls[0];
    expect(url).toBe('/api/publish/timetables/revision-edit/1/9/save/');
    expect(body.get('description')).toBe('New description');
    expect(body.get('short_description')).toBe('New short');
  });

  it('shows Django required messages without posting when fields are blank', async () => {
    await renderPage({ datasetType: 'fares', mode: 'live' });

    fireEvent.change(screen.getByLabelText('Data set description'), { target: { value: ' ' } });
    fireEvent.change(screen.getByLabelText('Data set short description'), { target: { value: '' } });
    fireEvent.click(screen.getByRole('button', { name: 'Save and continue' }));

    const summary = await screen.findByRole('alert');
    expect(within(summary).getByRole('link', { name: EDIT_DESCRIPTION_ERRORS.description })).toHaveAttribute(
      'href',
      '#id_description',
    );
    expect(
      within(summary).getByRole('link', { name: EDIT_DESCRIPTION_ERRORS.shortDescription }),
    ).toHaveAttribute('href', '#id_short_description');
    expect(summary).toHaveFocus();
    expect(screen.getByLabelText('Data set description')).toHaveClass('govuk-textarea--error');
    expect(screen.getByLabelText('Data set short description')).toHaveClass('govuk-input--error');
    expect(mockPost).not.toHaveBeenCalled();
  });

  it('shows Django field errors returned by the API', async () => {
    mockPost.mockRejectedValue(
      new ApiError('Description validation failed', 400, {
        short_description: ['Ensure this value has at most 30 characters (it has 31).'],
      }),
    );
    await renderPage({ datasetType: 'fares', mode: 'draft' });

    fireEvent.click(screen.getByRole('button', { name: 'Save and continue' }));

    const summary = await screen.findByRole('alert');
    expect(
      within(summary).getByRole('link', {
        name: 'Ensure this value has at most 30 characters (it has 31).',
      }),
    ).toHaveAttribute('href', '#id_short_description');
    expect(mockPush).not.toHaveBeenCalled();
  });

  it('shows the API error when the data set cannot be loaded', async () => {
    mockGet.mockRejectedValue(new ApiError('Dataset not found', 404, {}));

    render(<EditDescriptionContent datasetType="timetable" mode="live" />);

    expect(await screen.findByText('Dataset not found')).toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Edit description' })).not.toBeInTheDocument();
  });
});
