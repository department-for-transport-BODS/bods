/**
 * DatasetSearch Component Tests
 * 
 */

import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { DatasetSearch } from './DatasetSearch';

const mockPush = jest.fn();
const mockSearchParams = new URLSearchParams();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  usePathname: () => '/data',
  useSearchParams: () => mockSearchParams,
}));

describe('DatasetSearch', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchParams.delete('search');
    mockSearchParams.delete('page');
  });

  describe('rendering', () => {
    it('renders search input with label', () => {
      render(<DatasetSearch />);
      
      expect(screen.getByRole('searchbox')).toBeInTheDocument();
      expect(screen.getByText('Search datasets')).toBeInTheDocument();
    });

    it('renders search button', () => {
      render(<DatasetSearch />);
      
      expect(screen.getByRole('button', { name: /search/i })).toBeInTheDocument();
    });

    it('renders hint text', () => {
      render(<DatasetSearch />);
      
      expect(screen.getByText(/enter keywords to search/i)).toBeInTheDocument();
    });

    it('renders with custom props', () => {
      render(
        <DatasetSearch
          label="Custom label"
          hint="Custom hint"
          placeholder="Custom placeholder"
        />
      );
      
      expect(screen.getByLabelText(/custom label/i)).toBeInTheDocument();
      expect(screen.getByText(/custom hint/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/custom placeholder/i)).toBeInTheDocument();
    });

    it('shows initial search value from URL', () => {
      mockSearchParams.set('search', 'existing search');
      
      render(<DatasetSearch />);
      
      const input = screen.getByRole('searchbox');
      expect(input).toHaveValue('existing search');
    });
  });

  describe('search functionality', () => {
    it('updates input value on typing', async () => {
      const user = userEvent.setup();
      render(<DatasetSearch />);
      
      const input = screen.getByRole('searchbox');
      await user.type(input, 'bus routes');
      
      expect(input).toHaveValue('bus routes');
    });

    it('submits search on form submission', async () => {
      const user = userEvent.setup();
      render(<DatasetSearch />);
      
      const input = screen.getByRole('searchbox');
      await user.type(input, 'manchester');
      
      const form = screen.getByRole('search');
      fireEvent.submit(form);
      
      expect(mockPush).toHaveBeenCalledWith('/data?search=manchester');
    });

    it('submits search on button click', async () => {
      const user = userEvent.setup();
      render(<DatasetSearch />);
      
      const input = screen.getByRole('searchbox');
      await user.type(input, 'arriva');
      
      const button = screen.getByRole('button', { name: /^search$/i });
      await user.click(button);
      
      expect(mockPush).toHaveBeenCalledWith('/data?search=arriva');
    });

    it('trims whitespace from search query', async () => {
      const user = userEvent.setup();
      render(<DatasetSearch />);
      
      const input = screen.getByRole('searchbox');
      await user.type(input, '  london buses  ');
      
      const form = screen.getByRole('search');
      fireEvent.submit(form);
      
      expect(mockPush).toHaveBeenCalledWith('/data?search=london+buses');
    });

    it('resets page when searching', async () => {
      mockSearchParams.set('page', '3');
      const user = userEvent.setup();
      render(<DatasetSearch />);
      
      const input = screen.getByRole('searchbox');
      await user.type(input, 'test');
      
      const form = screen.getByRole('search');
      fireEvent.submit(form);
      
      expect(mockPush).toHaveBeenCalledWith('/data?search=test');
    });

    it('calls onSearch callback when provided', async () => {
      const onSearch = jest.fn();
      const user = userEvent.setup();
      render(<DatasetSearch onSearch={onSearch} />);
      
      const input = screen.getByRole('searchbox');
      await user.type(input, 'test query');
      
      const form = screen.getByRole('search');
      fireEvent.submit(form);
      
      expect(onSearch).toHaveBeenCalledWith('test query');
    });
  });

  describe('clear functionality', () => {
    it('shows clear button when search has value', async () => {
      const user = userEvent.setup();
      render(<DatasetSearch />);
      
      const input = screen.getByRole('searchbox');
      await user.type(input, 'test');
      
      expect(screen.getByRole('button', { name: /clear search/i })).toBeInTheDocument();
    });

    it('hides clear button when search is empty', () => {
      render(<DatasetSearch />);
      
      expect(screen.queryByRole('button', { name: /clear search/i })).not.toBeInTheDocument();
    });

    it('clears search on clear button click', async () => {
      const user = userEvent.setup();
      render(<DatasetSearch />);
      
      const input = screen.getByRole('searchbox');
      await user.type(input, 'test');
      
      const clearButton = screen.getByRole('button', { name: /clear search/i });
      await user.click(clearButton);
      
      expect(input).toHaveValue('');
      expect(mockPush).toHaveBeenCalledWith('/data');
    });

    it('clears search on Escape key', async () => {
      const user = userEvent.setup();
      render(<DatasetSearch />);
      
      const input = screen.getByRole('searchbox');
      await user.type(input, 'test');
      await user.keyboard('{Escape}');
      
      expect(input).toHaveValue('');
      expect(mockPush).toHaveBeenCalledWith('/data');
    });

    it('calls onSearch with empty string when cleared', async () => {
      const onSearch = jest.fn();
      const user = userEvent.setup();
      render(<DatasetSearch onSearch={onSearch} />);
      
      const input = screen.getByRole('searchbox');
      await user.type(input, 'test');
      
      const clearButton = screen.getByRole('button', { name: /clear search/i });
      await user.click(clearButton);
      
      expect(onSearch).toHaveBeenLastCalledWith('');
    });
  });

  describe('accessibility', () => {
    it('has proper form role', () => {
      render(<DatasetSearch />);
      
      expect(screen.getByRole('search')).toBeInTheDocument();
    });

    it('has proper aria-label on form', () => {
      render(<DatasetSearch />);
      
      const form = screen.getByRole('search');
      expect(form).toHaveAttribute('aria-label', 'Search datasets');
    });

    it('has proper aria-describedby on input', () => {
      render(<DatasetSearch />);
      
      const input = screen.getByRole('searchbox');
      expect(input).toHaveAttribute('aria-describedby', 'dataset-search-hint');
    });

    it('has screen reader announcement region', () => {
      render(<DatasetSearch />);
      
      const announcement = screen.getByRole('status');
      expect(announcement).toHaveClass('govuk-visually-hidden');
    });

    it('focuses input after clear', async () => {
      const user = userEvent.setup();
      render(<DatasetSearch />);
      
      const input = screen.getByRole('searchbox');
      await user.type(input, 'test');
      
      const clearButton = screen.getByRole('button', { name: /clear search/i });
      await user.click(clearButton);
      
      expect(document.activeElement).toBe(input);
    });
  });

  describe('URL state preservation', () => {
    it('preserves other query params when searching', async () => {
      mockSearchParams.set('filter', 'timetable');
      const user = userEvent.setup();
      render(<DatasetSearch />);
      
      const input = screen.getByRole('searchbox');
      await user.type(input, 'test');
      
      const form = screen.getByRole('search');
      fireEvent.submit(form);
      
      expect(mockPush).toHaveBeenCalledWith('/data?filter=timetable&search=test');
    });

    it('preserves other query params when clearing', async () => {
      mockSearchParams.set('filter', 'timetable');
      mockSearchParams.set('search', 'existing');
      const user = userEvent.setup();
      render(<DatasetSearch />);
      
      const clearButton = screen.getByRole('button', { name: /clear search/i });
      await user.click(clearButton);
      
      expect(mockPush).toHaveBeenCalledWith('/data?filter=timetable');
    });
  });
});

