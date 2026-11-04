import { render, screen, within } from '@testing-library/react';
import { Pagination } from './Pagination';
import { tablePageRange } from '@/lib/table-page-range';

let mockSearch = '';

jest.mock('next/navigation', () => ({
  useSearchParams: () => new URLSearchParams(mockSearch),
  usePathname: () => '/org/7/dataset/timetable',
}));

// Expected windows are the output of Django's paginator_range filter (transit_odp/common/templatetags).
describe('tablePageRange (Django paginator_range)', () => {
  it.each([
    [1, 1, [1]],
    [1, 5, [1, 2, 3, 4, 5]],
    [6, 10, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]],
    [1, 11, [1, 2, 3, 4, 5, 6, 7, 8, '...', 11]],
    [11, 11, [1, '...', 4, 5, 6, 7, 8, 9, 10, 11]],
  ])('page %i of %i', (current, total, expected) => {
    expect(tablePageRange(current, total)).toEqual(expected);
  });

  it('shows the first pages and a trailing gap on the first page of many', () => {
    expect(tablePageRange(1, 30)).toEqual([1, 2, 3, 4, 5, 6, '...', 30]);
  });

  it('shows a gap on both sides in the middle', () => {
    expect(tablePageRange(15, 30)).toEqual([1, '...', 13, 14, 15, 16, '...', 30]);
  });

  it('shows a leading gap and the final pages on the last page', () => {
    expect(tablePageRange(30, 30)).toEqual([1, '...', 25, 26, 27, 28, 29, 30]);
  });
});

describe('Pagination variant="table"', () => {
  beforeEach(() => {
    mockSearch = '';
  });

  const renderTable = (currentPage: number, totalPages: number) => {
    render(<Pagination variant="table" currentPage={currentPage} totalPages={totalPages} />);
    return screen.getByRole('navigation', { name: 'Pagination' });
  };

  const labels = (nav: HTMLElement) =>
    within(nav)
      .getAllByRole('listitem')
      .map((item) => item.textContent?.trim());

  it('shows a single page, as Django does, without Previous or Next', () => {
    const nav = renderTable(1, 1);

    expect(labels(nav)).toEqual(['1']);
    expect(nav.querySelector('.govuk-pagination__prev')).toBeNull();
    expect(nav.querySelector('.govuk-pagination__next')).toBeNull();
  });

  it('first page: no Previous, window then gap and last page, Next', () => {
    const nav = renderTable(1, 30);

    expect(labels(nav)).toEqual(['1', '2', '3', '4', '5', '6', '⋯', '30']);
    expect(nav.querySelector('a[rel="prev"]')).toBeNull();
    expect(nav.querySelector('a[rel="next"]')).toHaveAttribute('href', '?page=2');
    expect(nav.querySelector('.govuk-pagination__link-title')).toHaveTextContent('Next');
  });

  it('middle page: gaps either side, Previous and Next', () => {
    const nav = renderTable(15, 30);

    expect(labels(nav)).toEqual(['1', '⋯', '13', '14', '15', '16', '⋯', '30']);
    expect(nav.querySelector('a[rel="prev"]')).toHaveAttribute('href', '?page=14');
    expect(nav.querySelector('a[rel="next"]')).toHaveAttribute('href', '?page=16');
    expect(nav.querySelectorAll('.govuk-pagination__item--ellipses')).toHaveLength(2);
    expect(nav.querySelector('.govuk-pagination__item--current')).toHaveTextContent('15');
  });

  it('last page: Previous, no Next, leading gap', () => {
    const nav = renderTable(30, 30);

    expect(labels(nav)).toEqual(['1', '⋯', '25', '26', '27', '28', '29', '30']);
    expect(nav.querySelector('a[rel="prev"]')).toHaveAttribute('href', '?page=29');
    expect(nav.querySelector('a[rel="next"]')).toBeNull();
  });

  it('lists every page when there are ten or fewer', () => {
    const nav = renderTable(4, 10);

    expect(labels(nav)).toHaveLength(10);
    expect(nav.querySelector('.govuk-pagination__item--ellipses')).toBeNull();
  });

  it('puts the page first and keeps other query parameters, like relative_url', () => {
    mockSearch = 'tab=draft&sort=-name&page=3';
    const nav = renderTable(3, 5);

    const hrefs = Array.from(nav.querySelectorAll('li a')).map((a) => a.getAttribute('href'));
    expect(hrefs[0]).toBe('?page=1&tab=draft&sort=-name');
    expect(hrefs[4]).toBe('?page=5&tab=draft&sort=-name');
  });

  it('matches the Django markup for the nav and links', () => {
    const nav = renderTable(2, 3);

    expect(nav).toHaveAttribute('role', 'navigation');
    expect(nav).toHaveClass('justify-center-l', 'govuk-pagination');
    expect(nav.querySelector('.govuk-pagination__prev svg.govuk-pagination__icon--prev')).not.toBeNull();
    expect(nav.querySelector('.govuk-pagination__next svg.govuk-pagination__icon--next')).not.toBeNull();
  });
});

describe('Pagination default variant', () => {
  it('is unchanged: still shows a ±2 window with Go to page labels', () => {
    mockSearch = '';
    render(<Pagination currentPage={15} totalPages={30} />);

    const nav = screen.getByRole('navigation', { name: 'Pagination' });
    expect(within(nav).getByRole('link', { name: 'Go to page 13' })).toBeInTheDocument();
    expect(within(nav).getByRole('link', { name: 'Go to page 17' })).toBeInTheDocument();
    expect(within(nav).queryByRole('link', { name: 'Go to page 18' })).not.toBeInTheDocument();
  });

  it('renders nothing for a single page unless showSinglePage is set', () => {
    mockSearch = '';
    const { container } = render(<Pagination currentPage={1} totalPages={1} />);

    expect(container).toBeEmptyDOMElement();
  });
});
