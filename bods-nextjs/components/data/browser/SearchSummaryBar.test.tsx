import { render, screen, within } from '@testing-library/react';
import { SearchSummaryBar } from './SearchSummaryBar';

describe('SearchSummaryBar', () => {
  it('keeps the summary bar visible when no search or filters are active', () => {
    render(<SearchSummaryBar />);

    const summary = screen.getByRole('region', { name: 'Search filters' });
    expect(summary).toBeInTheDocument();
    expect(within(summary).queryByText('Containing')).not.toBeInTheDocument();
    expect(screen.getByRole('separator')).toHaveClass('pillbox-break');
  });

  it('shows a containing label and removable, black-style search term', () => {
    render(
      <SearchSummaryBar
        searchTerm="Aguilar"
        clearSearchHref="/operators/?ordering=name"
        showContaining
      />,
    );

    const summary = screen.getByRole('region', { name: 'Search filters' });
    expect(within(summary).getByText('Containing')).toBeInTheDocument();
    expect(within(summary).getByText('Aguilar')).toHaveClass('app-data-browser__filter-pill-label');
    expect(within(summary).getByRole('link', { name: 'Aguilar' })).toHaveAttribute(
      'href',
      '/operators?ordering=name',
    );
  });

  it('shows filter pills without adding the containing label', () => {
    render(<SearchSummaryBar filters={[{ key: 'status', label: 'Published', href: '/timetable/' }]} />);

    const summary = screen.getByRole('region', { name: 'Search filters' });
    expect(within(summary).getByText('Published')).toHaveClass('app-data-browser__filter-pill-label');
    expect(within(summary).queryByText('Containing')).not.toBeInTheDocument();
  });
});
