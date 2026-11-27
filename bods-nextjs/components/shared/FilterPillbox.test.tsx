import { render, screen, within } from '@testing-library/react';
import { FilterPillbox } from './FilterPillbox';

describe('FilterPillbox', () => {
  it('stays visible when no search or filters are active', () => {
    render(<FilterPillbox searchLabel="Containing" />);

    const summary = screen.getByRole('region', { name: 'Search filters' });
    expect(summary).toHaveClass('search-pillbox');
    expect(within(summary).queryByText('Containing')).not.toBeInTheDocument();
    expect(screen.getByRole('separator')).toHaveClass('pillbox-break');
  });

  it('shows the search label and a removable search-term pill', () => {
    render(
      <FilterPillbox searchLabel="Containing" searchTerm="Aguilar" clearSearchHref="/operators/?ordering=name" />,
    );

    const summary = screen.getByRole('region', { name: 'Search filters' });
    expect(within(summary).getByText('Containing')).toBeInTheDocument();
    expect(within(summary).getByText('Aguilar')).toHaveClass('pill-item__label');
    expect(within(summary).getByRole('link', { name: 'Aguilar' })).toHaveAttribute(
      'href',
      '/operators?ordering=name',
    );
  });

  it('supports the site admin "Beginning" label', () => {
    render(<FilterPillbox searchLabel="Beginning" searchTerm="A" clearSearchHref="?q=" />);

    expect(screen.getByText('Beginning')).toBeInTheDocument();
  });

  it('shows filter pills and a title without a search label', () => {
    render(
      <FilterPillbox
        title="Filtered by"
        searchLabel="Containing"
        filters={[{ key: 'status', label: 'Published', href: '/timetable/' }]}
      />,
    );

    const summary = screen.getByRole('region', { name: 'Search filters' });
    expect(within(summary).getByText('Filtered by')).toBeInTheDocument();
    expect(within(summary).getByText('Published')).toHaveClass('pill-item__label');
    expect(within(summary).queryByText('Containing')).not.toBeInTheDocument();
  });
});
