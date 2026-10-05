import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { Timetable, TimetableDirection } from './line-detail-types';
import { TimetableVisualiser } from './TimetableVisualiser';

const mockPush = jest.fn();
let mockSearchParams = new URLSearchParams('line=1&service=PB1%3A1');

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => mockSearchParams,
}));

jest.mock('air-datepicker', () => ({
  __esModule: true,
  default: class {
    destroy() {}
  },
}));
jest.mock('air-datepicker/locale/en', () => ({ __esModule: true, default: {} }));

function direction(overrides: Partial<TimetableDirection> = {}): TimetableDirection {
  return {
    direction: 'outbound',
    journeyName: 'Outbound - A to B',
    isEmpty: false,
    totalPage: 2,
    currPage: 1,
    showAll: false,
    totalRowCount: 12,
    pageParam: 'outbound_page',
    showAllParam: 'showAllOutbound',
    columns: [
      { name: 'Journey Code', observation: null },
      { name: 'JC1', observation: null },
    ],
    rows: [
      {
        index: 0,
        stop: {
          name: 'High Street',
          atcoCode: '0100BRP90310',
          street: 'High St',
          indicator: 'Stop A',
          stopType: 'BCT',
          observation: null,
        },
        cells: [
          {
            departureTime: '07:00',
            journeyId: 5,
            observations: [{ title: 'Late journey', text: 'Too late', resolve: 'Fix it' }],
          },
        ],
      },
    ],
    ...overrides,
  };
}

function renderVisualiser(timetable: Timetable, feedbackUrl: string | null = '/feedback/', renderEmpty = true) {
  return render(
    <TimetableVisualiser timetable={timetable} feedbackUrl={feedbackUrl} renderEmptyDirections={renderEmpty} />,
  );
}

const timetable: Timetable = {
  currDate: '2024-05-01',
  isTimetableInfoAvailable: true,
  directions: [
    direction(),
    direction({ direction: 'inbound', journeyName: 'Inbound - B to A', isEmpty: true, rows: [], totalPage: 0, totalRowCount: 0 }),
  ],
};

describe('TimetableVisualiser', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchParams = new URLSearchParams('line=1&service=PB1%3A1');
  });

  it('shows the inset text when no timetable is available for the date', () => {
    renderVisualiser({ ...timetable, isTimetableInfoAvailable: false });

    expect(
      screen.getByText('There is no timetable information available to view for this date. Please select another date.'),
    ).toBeInTheDocument();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });

  it('renders empty directions only when asked to', () => {
    const { unmount } = renderVisualiser(timetable, null, true);
    expect(screen.getByText('Inbound - B to A')).toBeInTheDocument();
    unmount();

    renderVisualiser(timetable, null, false);
    expect(screen.getByText('Outbound - A to B')).toBeInTheDocument();
    expect(screen.queryByText('Inbound - B to A')).not.toBeInTheDocument();
  });

  it('keeps the current query in see-more and pagination links', () => {
    renderVisualiser(timetable);

    expect(screen.getByRole('link', { name: 'See more' })).toHaveAttribute(
      'href',
      '?line=1&service=PB1%3A1&showAllOutbound=True',
    );
    expect(screen.getByRole('link', { name: /Next/ })).toHaveAttribute(
      'href',
      '?line=1&service=PB1%3A1&outbound_page=2',
    );
    expect(screen.queryByRole('link', { name: /Previous/ })).not.toBeInTheDocument();
  });

  it('opens one tooltip at a time and only closes it from its trigger or Close button', async () => {
    const user = userEvent.setup();
    renderVisualiser(timetable);
    const stop = screen.getByRole('button', { name: /High Street/ });
    const time = screen.getByRole('button', { name: /07:00/ });
    const stopTooltip = document.getElementById('tooltip-outbound-0') as HTMLElement;

    await user.click(stop);
    expect(stop).toHaveAttribute('aria-expanded', 'true');
    expect(stopTooltip).toHaveClass('showtooltip');

    await user.click(document.body);
    await user.click(within(stopTooltip).getByText('ATCO Code:', { exact: false }));
    expect(stop).toHaveAttribute('aria-expanded', 'true');

    await user.click(time);
    expect(stop).toHaveAttribute('aria-expanded', 'false');
    expect(time).toHaveAttribute('aria-expanded', 'true');

    const timeTooltip = document.getElementById('5-0') as HTMLElement;
    await user.click(within(timeTooltip).getByRole('button', { name: 'Close' }));
    expect(time).toHaveAttribute('aria-expanded', 'false');
  });

  it('builds Add Feedback links from the current query, and hides them without a feedback URL', () => {
    const { unmount } = renderVisualiser(timetable);
    const stopTooltip = document.getElementById('tooltip-outbound-0') as HTMLElement;
    expect(within(stopTooltip).getByRole('link', { name: 'Add Feedback' })).toHaveAttribute(
      'href',
      '/feedback/?line=1&service=PB1%3A1&stop=High+Street&direction=outbound&atco_code=0100BRP90310',
    );
    const journeyTooltip = document.getElementById('jc-outbound-1') as HTMLElement;
    expect(within(journeyTooltip).getByRole('link', { name: 'Add Feedback' })).toHaveAttribute(
      'href',
      '/feedback/?line=1&service=PB1%3A1&journey_code=JC1&direction=outbound',
    );
    unmount();

    renderVisualiser(timetable, null);
    expect(screen.queryByRole('link', { name: 'Add Feedback' })).not.toBeInTheDocument();
  });

  it('applies a valid date filter as an ISO date and ignores invalid input', async () => {
    const user = userEvent.setup();
    renderVisualiser(timetable);
    const input = screen.getByLabelText('Date');

    await user.clear(input);
    await user.type(input, 'not a date');
    await user.click(screen.getByRole('button', { name: 'Apply Filter' }));
    expect(mockPush).not.toHaveBeenCalled();

    await user.clear(input);
    await user.type(input, '03/02/2024');
    await user.click(screen.getByRole('button', { name: 'Apply Filter' }));
    expect(mockPush).toHaveBeenCalledWith('?line=1&service=PB1%3A1&date=2024-02-03');
  });

  it('always shows the Timetable heading above the date filter', () => {
    renderVisualiser(timetable);

    expect(screen.getByRole('heading', { name: 'Timetable' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Filter by' })).toBeInTheDocument();
  });
});
