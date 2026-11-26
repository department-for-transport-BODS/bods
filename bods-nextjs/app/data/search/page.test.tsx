import { fireEvent, render, screen, within } from '@testing-library/react';
import { TRANSXCHANGE_VERSION } from '@/config/client';
import DataSearchSelectPage from './page';

const PTI_URL = 'https://example.test/pti.pdf';

jest.mock('next/server', () => ({ connection: jest.fn().mockResolvedValue(undefined) }));
jest.mock('@/config/server', () => ({ serverConfig: { ptiPdfUrl: 'https://example.test/pti.pdf' } }));

async function renderPage() {
  return render(await DataSearchSelectPage());
}

describe('DataSearchSelectPage', () => {
  it('renders the Django format labels with a space before the colon', async () => {
    await renderPage();

    expect(screen.getAllByText('Format :')).toHaveLength(4);
    expect(screen.getAllByText('File type :')).toHaveLength(4);
    expect(screen.getAllByText('Data type :')).toHaveLength(4);
    expect(screen.getAllByText('Data source :')).toHaveLength(4);
  });

  it('shows the Django TXC profile text', async () => {
    const { container } = await renderPage();

    expect(container).toHaveTextContent(`Format : TXC ${TRANSXCHANGE_VERSION} PTI 1.1.A`);
  });

  it('renders a help icon next to each format, matching Django', async () => {
    await renderPage();

    expect(screen.getAllByRole('button', { name: /^Help: / }).map((el) => el.getAttribute('aria-label'))).toEqual([
      'Help: TransXChange',
      'Help: SIRI-VM',
      'Help: NeTEx',
      'Help: SIRI-SX',
    ]);
  });

  it('opens the TransXChange help modal linking to the PTI profile', async () => {
    await renderPage();

    const overlay = screen.getAllByTestId('help-overlay')[0];
    expect(overlay).not.toHaveClass('active');

    fireEvent.click(screen.getByRole('button', { name: 'Help: TransXChange' }));

    expect(overlay).toHaveClass('active');
    expect(screen.getByRole('heading', { name: 'TransXChange' })).toBeInTheDocument();
    expect(within(overlay).getByRole('link', { name: 'found here' })).toHaveAttribute('href', PTI_URL);
  });
});
