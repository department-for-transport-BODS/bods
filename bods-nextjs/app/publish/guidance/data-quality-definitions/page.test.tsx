import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import DataQualityDefinitionsPage from './page';
import { api } from '@/lib/api-client';

jest.mock('@/lib/api-client', () => ({
  api: { get: jest.fn() },
}));

const mockGet = api.get as jest.Mock;

const observation = (title: string, overrides = {}) => ({
  title,
  level: 'Critical',
  text: `${title} text`,
  impacts: `${title} impacts`,
  resolve: null,
  preamble: null,
  isActive: true,
  extraInfo: [],
  ...overrides,
});

describe('Data quality observation definitions page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    window.history.replaceState(null, '', '/');
    mockGet.mockResolvedValue({
      levels: [
        {
          level: 'Critical',
          count: 2,
          intro: null,
          categories: [
            {
              type: 'Stop',
              showCategory: true,
              observations: [
                observation('Incorrect stop type', { extraInfo: [{ code: 'BCT', description: 'On-street bus stop' }] }),
                observation('Missing stop', { isActive: false }),
              ],
            },
          ],
        },
        {
          level: 'Advisory',
          count: 1,
          intro: null,
          categories: [{ type: 'Journey', showCategory: true, observations: [observation('Duplicate journey code')] }],
        },
      ],
    });
  });

  it('renders critical observation definitions by category', async () => {
    render(<DataQualityDefinitionsPage />);

    expect(screen.getByRole('heading', { name: 'Observation definitions', level: 1 })).toBeInTheDocument();
    expect(mockGet).toHaveBeenCalledWith('/api/publish/data-quality/definitions/');
    expect(screen.getByRole('link', { name: "View Department for Transport's TransXChange Schema Guide" })).toHaveAttribute(
      'href',
      'https://www.gov.uk/government/collections/transxchange',
    );

    const panel = await screen.findByRole('tabpanel');
    expect(within(panel).getByRole('heading', { name: 'Critical observations (2)' })).toBeInTheDocument();
    expect(within(panel).getByRole('heading', { name: 'Stop' })).toBeInTheDocument();
    expect(within(panel).getByText('COMING SOON')).toBeInTheDocument();

    await userEvent.click(within(panel).getByText('Incorrect stop type'));
    expect(within(panel).getByText('Incorrect stop type text')).toBeVisible();
    expect(within(panel).getByRole('cell', { name: 'BCT' })).toBeInTheDocument();
  });

  it('switches to advisory observations', async () => {
    render(<DataQualityDefinitionsPage />);

    await userEvent.click(await screen.findByRole('tab', { name: 'Advisory observations' }));

    const panel = screen.getByRole('tabpanel');
    expect(within(panel).getByRole('heading', { name: 'Advisory observations (1)' })).toBeInTheDocument();
    expect(within(panel).getByText('Duplicate journey code')).toBeInTheDocument();
  });

  it('selects a linked definition tab and supports keyboard navigation', async () => {
    window.history.replaceState(null, '', '/#advisory');
    render(<DataQualityDefinitionsPage />);
    const advisory = await screen.findByRole('tab', { name: 'Advisory observations' });
    expect(advisory).toHaveAttribute('aria-selected', 'true');
    advisory.focus();

    await userEvent.keyboard('{ArrowLeft}');
    const critical = screen.getByRole('tab', { name: 'Critical observations' });
    expect(critical).toHaveFocus();
    expect(critical).toHaveAttribute('aria-selected', 'true');
    expect(window.location.hash).toBe('#critical');
  });
});
