import { render, screen } from '@testing-library/react';
import { DataBrowserResultCard } from './DataBrowserResultCard';

describe('DataBrowserResultCard', () => {
  it('renders the title link and key/value rows', () => {
    render(
      <DataBrowserResultCard
        title="Aberdeen City Council"
        href="/local-authority/detail"
        keyValues={[{ key: 'Services requiring attention:', value: '0 %' }]}
      />,
    );

    expect(screen.getByRole('link', { name: 'Aberdeen City Council' })).toHaveAttribute('href', '/local-authority/detail');
    expect(screen.getByText('Services requiring attention:')).toBeInTheDocument();
    expect(screen.getByText('0 %')).toBeInTheDocument();
  });

  it('separates the key and value with a space, as Django key-value-list inline-blocks do', () => {
    render(<DataBrowserResultCard title="Operator" href="/operators/1" keyValues={[{ key: 'Date registered:', value: '5 October 2026' }]} />);

    expect(screen.getByRole('listitem')).toHaveTextContent('Date registered: 5 October 2026');
  });
});
