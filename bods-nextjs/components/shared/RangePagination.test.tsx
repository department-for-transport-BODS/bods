import { render, screen } from '@testing-library/react';
import { RangePagination } from './RangePagination';

const buildHref = (page: number) => `/operators?page=${page}`;

describe('RangePagination', () => {
  it('shows only Next on the first page', () => {
    render(<RangePagination currentPage={1} numPages={3} pageRange={[1, 2, 3]} buildHref={buildHref} />);

    expect(screen.queryByText(/Previous/)).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Next/ })).toHaveAttribute('href', '/operators?page=2');
  });

  it('shows Previous and Next in the middle and marks the current page', () => {
    render(<RangePagination currentPage={2} numPages={3} pageRange={[1, 2, 3]} buildHref={buildHref} />);

    expect(screen.getByRole('link', { name: /Previous/ })).toHaveAttribute('href', '/operators?page=1');
    expect(screen.getByRole('link', { name: /Next/ })).toHaveAttribute('href', '/operators?page=3');
    expect(screen.getByRole('link', { name: 'Page 2' }).closest('li')).toHaveClass(
      'govuk-pagination__item--current',
    );
  });

  it('renders "..." gaps as an ellipsis item', () => {
    render(
      <RangePagination currentPage={1} numPages={9} pageRange={[1, 2, 3, '...', 9]} buildHref={buildHref} />,
    );

    expect(screen.getByText('⋯')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Page 9' })).toHaveAttribute('href', '/operators?page=9');
  });
});
