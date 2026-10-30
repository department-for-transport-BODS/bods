import { render, screen, within } from '@testing-library/react';
import { publishPath } from '@/config/client';
import { FaresDatasetDetailContent } from './FaresDatasetDetailContent';
import type { FaresDatasetDetail } from './types';

jest.mock('@/components/data/MapboxFaresStopMap', () => ({
  MapboxFaresStopMap: ({ revisionId }: { revisionId: number }) => (
    <div id="map" data-testid="map" data-revision={revisionId} />
  ),
}));

const dataset: FaresDatasetDetail = {
  id: 8,
  name: 'Fares data set',
  description: 'A description',
  organisationId: 3,
  organisationName: 'Local Import Org',
  status: 'live',
  revisionId: 21,
  transxchangeVersion: '',
  uploadFileExtension: 'zip',
  lastUpdated: '22 Feb 2026 10:30',
  publishedBy: 'someone',
  showMap: true,
  isCompliantError: false,
  showReportLink: false,
  metadata: {
    schemaVersion: '1.1',
    numOfFareZones: '4',
    numOfLines: '5',
    numOfSalesOfferPackages: '6',
    numOfFareProducts: '7',
    numOfUserProfiles: '8',
    validFrom: '1 Jan 2026',
    validTo: 'None',
  },
  isSubscribed: false,
  feedApi: null,
};

function renderContent(overrides: Partial<FaresDatasetDetail> = {}, isFaresValidatorActive = false) {
  return render(
    <FaresDatasetDetailContent
      dataset={{ ...dataset, ...overrides }}
      isFaresValidatorActive={isFaresValidatorActive}
    />,
  );
}

function rowFor(header: string) {
  return screen.getByRole('rowheader', { name: new RegExp(`^${header}`) }).closest('tr') as HTMLElement;
}

describe('FaresDatasetDetailContent (success)', () => {
  it('renders the Django property table rows in order (validator flag off: no compliance row)', () => {
    const { container } = renderContent();

    const headers = Array.from(container.querySelectorAll('table.consumer-property-table th')).map((th) =>
      th.textContent?.trim(),
    );
    expect(headers).toEqual([
      'Name',
      'Data type',
      'Data set ID',
      'Description',
      'Owner',
      'Status',
      'NeTEx Version',
      'Last updated',
      'Number of fare zones',
      'Number of lines',
      'Number of sales offer packages',
      'Number of fare products',
      'Number of user types',
      'Earliest start date',
      'Earliest end date',
    ]);
    expect(within(rowFor('Data type')).getByText('Fares data')).toBeInTheDocument();
    expect(within(rowFor('NeTEx Version')).getByText('1.1')).toBeInTheDocument();
    expect(within(rowFor('Number of fare zones')).getByText('4')).toBeInTheDocument();
    expect(within(rowFor('Number of user types')).getByText('8')).toBeInTheDocument();
    expect(within(rowFor('Earliest start date')).getByText('1 Jan 2026')).toBeInTheDocument();
    expect(within(rowFor('Earliest end date')).getByText('None')).toBeInTheDocument();
  });

  it('links the owner to their live fares and links the change log', () => {
    renderContent();

    expect(screen.getByRole('link', { name: 'Local Import Org' })).toHaveAttribute(
      'href',
      expect.stringContaining('/fares?organisation=3&status=live'),
    );
    expect(screen.getByRole('link', { name: 'View change log' })).toHaveAttribute(
      'href',
      expect.stringContaining('/fares/dataset/8/changelog'),
    );
  });

  it('adds the BODS Compliant data row first after Status when the validator flag is on', () => {
    const { container } = renderContent({}, true);

    const headers = Array.from(container.querySelectorAll('table.consumer-property-table th')).map((th) =>
      th.textContent?.trim(),
    );
    expect(headers.slice(5, 8)).toEqual(['Status', 'BODS Compliant data', 'NeTEx Version']);
    expect(within(rowFor('BODS Compliant data')).getByText('Compliant')).toHaveClass('item__value');
  });

  it('shows Non compliant with the report link when compliance fails and a report exists', () => {
    renderContent({ isCompliantError: true, showReportLink: true }, true);
    const row = rowFor('BODS Compliant data');

    expect(within(row).getByText('Non compliant')).toBeInTheDocument();
    expect(within(row).getByText('!')).toHaveClass('govuk-warning-text__icon');
    expect(within(row).getByRole('link', { name: 'Download validation report' })).toHaveAttribute(
      'href',
      publishPath('/org/3/dataset/fares-validator/21/export/'),
    );
  });

  it('shows Non compliant without a report link when there is no validation result', () => {
    renderContent({ isCompliantError: true, showReportLink: false }, true);
    const row = rowFor('BODS Compliant data');

    expect(within(row).getByText('Non compliant')).toBeInTheDocument();
    expect(within(row).queryByRole('link')).not.toBeInTheDocument();
  });

  it('ignores compliance data entirely when the validator flag is off', () => {
    renderContent({ isCompliantError: true, showReportLink: true }, false);

    expect(screen.queryByText('BODS Compliant data')).not.toBeInTheDocument();
    expect(screen.queryByText('Non compliant')).not.toBeInTheDocument();
  });

  it.each(['live', 'inactive', 'expired'])(
    'starts the stop map for the live revision when status is %s',
    (status) => {
      renderContent({ status, showMap: true });

      expect(screen.getByTestId('map')).toHaveAttribute('data-revision', '21');
    },
  );

  it('renders an empty #map container without starting the map when showMap is false', () => {
    const { container } = renderContent({ showMap: false });

    expect(screen.queryByTestId('map')).not.toBeInTheDocument();
    expect(container.querySelector('#map.disruptions-width')).not.toBeNull();
  });

  it('hides the API URL panel for anonymous visitors and shows it when signed in', () => {
    const { unmount } = renderContent({ feedApi: null });
    expect(screen.queryByText('Use this data set in your code')).not.toBeInTheDocument();
    unmount();

    renderContent({
      feedApi: 'https://data.example/api/v1/fares/dataset/?api_key=abc',
    });
    expect(screen.getByRole('heading', { name: 'Use this data set in your code' })).toBeInTheDocument();
  });

  it('offers subscribe and download with the live revision file extension', () => {
    renderContent({ uploadFileExtension: 'xml' });

    expect(screen.getByRole('heading', { name: 'Subscribe, download the data' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Subscribe to this data set' })).toHaveAttribute(
      'href',
      expect.stringContaining('/fares/dataset/8/subscription'),
    );
    expect(screen.getByRole('link', { name: 'Download dataset (.xml)' })).toHaveAttribute(
      'href',
      expect.stringContaining('/fares/dataset/8/download'),
    );
  });

  it('always shows the data set feedback link', () => {
    renderContent();

    expect(screen.getByRole('link', { name: 'Contact data set owner directly' })).toHaveAttribute(
      'href',
      expect.stringContaining('/fares/dataset/8/feedback'),
    );
  });
});

describe('FaresDatasetDetailContent (error panel)', () => {
  it('replaces the success content with Django’s error panel when the status is error', () => {
    const { container } = renderContent({ status: 'error', transxchangeVersion: '2.4' }, true);

    expect(screen.getByRole('heading', { name: 'Data feed not available' })).toBeInTheDocument();
    expect(screen.queryByText('BODS Compliant data')).not.toBeInTheDocument();
    expect(container.querySelector('#map')).toBeNull();
    expect(screen.getByText('Fares data set')).toBeInTheDocument();
    expect(screen.getByText('22 Feb 2026 10:30 by someone')).toBeInTheDocument();
    expect(screen.getByText('2.4')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'View change log' })).toHaveAttribute(
      'href',
      expect.stringContaining('/fares/dataset/8/changelog'),
    );
    expect(screen.getByRole('link', { name: 'Download .xml (TransXChange format)' })).toHaveAttribute(
      'href',
      expect.stringContaining('/timetable/dataset/8/download/?get_working=true'),
    );
    expect(
      screen.getByRole('heading', {
        name: 'Would you like to provide feedback on this data set?',
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Provide feedback' })).toHaveAttribute(
      'href',
      expect.stringContaining('/fares/dataset/8/feedback'),
    );
  });

  it('shows "System" when nobody published the revision', () => {
    renderContent({ status: 'error', publishedBy: null });

    expect(screen.getByText('22 Feb 2026 10:30 by System')).toBeInTheDocument();
  });
});
