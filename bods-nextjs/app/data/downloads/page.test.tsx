import { fireEvent, render, screen, within } from '@testing-library/react';
import { DownloadsContent } from './_components/DownloadsContent';
import { dataPath, HOSTS, wwwPath } from '@/config/client';

const PTI_URL = 'https://example.test/pti.pdf';

function renderPage(isGtfsServiceAlertsLive = false) {
  return render(
    <DownloadsContent isGtfsServiceAlertsLive={isGtfsServiceAlertsLive} ptiPdfUrl={PTI_URL} />,
  );
}

describe('DownloadsContent', () => {
  it('breadcrumbs back through the Find service to Download All Data', () => {
    renderPage();

    expect(screen.getByRole('link', { name: 'Bus Open Data Service' })).toHaveAttribute(
      'href',
      HOSTS.www,
    );
    expect(screen.getByRole('link', { name: 'Find Bus Open Data' })).toHaveAttribute(
      'href',
      HOSTS.data,
    );
    expect(screen.getByRole('link', { name: 'Download All Data' })).toHaveAttribute(
      'href',
      dataPath('/downloads'),
    );
  });

  it('renders the Django heading, catalogue link and help links', () => {
    renderPage();

    expect(screen.getByRole('heading', { level: 1, name: 'Heading Title' })).toHaveTextContent(
      'Download all data',
    );
    expect(screen.getByRole('link', { name: 'Download the data catalogue' })).toHaveAttribute(
      'href',
      dataPath('/catalogue'),
    );
    expect(screen.getByRole('link', { name: 'Guide me' })).toHaveAttribute(
      'href',
      dataPath('/guide-me'),
    );
    expect(
      screen.getByRole('link', { name: 'Contact us for technical issues' }),
    ).toHaveAttribute('href', wwwPath('/contact'));
  });

  it('links each dataset type to its Django download URL', () => {
    renderPage();

    expect(screen.getByRole('link', { name: 'Timetables data' })).toHaveAttribute(
      'href',
      dataPath('/timetable/download/'),
    );
    expect(screen.getByRole('link', { name: 'Location data' })).toHaveAttribute(
      'href',
      dataPath('/avl/download/'),
    );
    expect(screen.getByRole('link', { name: 'Fares data' })).toHaveAttribute(
      'href',
      dataPath('/fares/download/'),
    );
    expect(screen.getByRole('link', { name: 'Disruptions data' })).toHaveAttribute(
      'href',
      dataPath('/disruptions/download/'),
    );
    expect(screen.getByRole('link', { name: 'Coach data' })).toHaveAttribute(
      'href',
      dataPath('/coach/download'),
    );
  });

  it('describes SIRI-SX only when GTFS service alerts are not live', () => {
    renderPage(false);

    expect(
      screen.getByText('Download disruptions data for selected regions in SIRI-SX format.'),
    ).toBeInTheDocument();
    expect(screen.getAllByRole('heading', { level: 1, name: 'GTFS-RT' })).toHaveLength(1);
  });

  it('describes SIRI-SX and GTFS-RT when GTFS service alerts are live', () => {
    renderPage(true);

    expect(
      screen.getByText(
        'Download disruptions data for selected regions in SIRI-SX and GTFS-RT formats.',
      ),
    ).toBeInTheDocument();
    // AVL + disruptions both include the GTFS-RT help modal.
    expect(screen.getAllByRole('heading', { level: 1, name: 'GTFS-RT' })).toHaveLength(2);
  });

  it('points the TransXChange help at the configured PTI profile', () => {
    renderPage();

    const overlay = screen.getAllByTestId('help-overlay')[0];
    expect(within(overlay).getByRole('heading', { name: 'TransXChange' })).toBeInTheDocument();
    expect(within(overlay).getByRole('link', { name: 'found here' })).toHaveAttribute(
      'href',
      PTI_URL,
    );
  });

  it('opens a help modal from its icon and closes it with the Close button', () => {
    renderPage();

    const overlay = screen.getAllByTestId('help-overlay')[0];
    expect(overlay).not.toHaveClass('active');

    fireEvent.click(screen.getAllByRole('button', { name: 'Help: TransXChange' })[0]);
    expect(overlay).toHaveClass('active');

    fireEvent.click(within(overlay).getByRole('button', { name: 'Close' }));
    expect(overlay).not.toHaveClass('active');
  });

  it('closes a help modal when the overlay backdrop is clicked', () => {
    renderPage();

    const overlay = screen.getAllByTestId('help-overlay')[0];
    fireEvent.click(screen.getAllByRole('button', { name: 'Help: TransXChange' })[0]);
    fireEvent.click(overlay);

    expect(overlay).not.toHaveClass('active');
  });
});
