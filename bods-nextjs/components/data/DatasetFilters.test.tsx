/**
 * Dataset Filters Component Tests
 * 
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import { DatasetFilters } from './DatasetFilters';
import type { FilterOption } from './DatasetFilters';

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  usePathname: jest.fn(),
  useSearchParams: jest.fn(),
}));

const mockRouter = {
  push: jest.fn(),
};

const mockSearchParams = new URLSearchParams();

const mockAreas: FilterOption[] = [
  { value: '1', label: 'London' },
  { value: '2', label: 'Manchester' },
  { value: '3', label: 'Birmingham' },
];

const mockOrganisations: FilterOption[] = [
  { value: '10', label: 'Operator A' },
  { value: '11', label: 'Operator B' },
  { value: '12', label: 'Operator C' },
];

describe('DatasetFilters', () => {
  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (usePathname as jest.Mock).mockReturnValue('/data');
    (useSearchParams as jest.Mock).mockReturnValue(mockSearchParams);
    mockRouter.push.mockClear();
    mockSearchParams.delete('area');
    mockSearchParams.delete('organisation');
    mockSearchParams.delete('status');
    mockSearchParams.delete('dataType');
  });

  it('renders all filter options', () => {
    render(
      <DatasetFilters
        areas={mockAreas}
        organisations={mockOrganisations}
      />
    );

    expect(screen.getByText('Filter by')).toBeInTheDocument();
    expect(screen.getByLabelText('Geographical area')).toBeInTheDocument();
    expect(screen.getByLabelText('Publisher')).toBeInTheDocument();
    expect(screen.getByLabelText('Status')).toBeInTheDocument();
    expect(screen.getByLabelText('Data type')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Apply filter' })).toBeInTheDocument();
  });

  it('populates dropdowns with provided options', () => {
    render(
      <DatasetFilters
        areas={mockAreas}
        organisations={mockOrganisations}
      />
    );

    const areaSelect = screen.getByLabelText('Geographical area') as HTMLSelectElement;
    expect(areaSelect.options).toHaveLength(4); // "All" + 3 areas
    expect(areaSelect.options[1].text).toBe('London');
    expect(areaSelect.options[2].text).toBe('Manchester');

    const orgSelect = screen.getByLabelText('Publisher') as HTMLSelectElement;
    expect(orgSelect.options).toHaveLength(4); // "All" + 3 orgs
    expect(orgSelect.options[1].text).toBe('Operator A');
  });

  it('updates URL when filter is changed', async () => {
    render(
      <DatasetFilters
        areas={mockAreas}
        organisations={mockOrganisations}
      />
    );

    const areaSelect = screen.getByLabelText('Geographical area');
    fireEvent.change(areaSelect, { target: { value: '1' } });

    await waitFor(() => {
      expect(mockRouter.push).toHaveBeenCalledWith(
        expect.stringContaining('area=1')
      );
    });
  });

  it('shows clear all button when filters are active', () => {
    mockSearchParams.set('area', '1');
    
    const { rerender } = render(
      <DatasetFilters
        areas={mockAreas}
        organisations={mockOrganisations}
      />
    );

    expect(screen.queryByRole('button', { name: 'Clear all filters' })).not.toBeInTheDocument();

    const areaSelect = screen.getByLabelText('Geographical area');
    fireEvent.change(areaSelect, { target: { value: '1' } });

    mockSearchParams.set('area', '1');
    (useSearchParams as jest.Mock).mockReturnValue(mockSearchParams);
    
    rerender(
      <DatasetFilters
        areas={mockAreas}
        organisations={mockOrganisations}
      />
    );

    expect(screen.getByRole('button', { name: 'Clear all filters' })).toBeInTheDocument();
  });

  it('clears all filters when clear button is clicked', async () => {
    mockSearchParams.set('area', '1');
    mockSearchParams.set('status', 'live');

    render(
      <DatasetFilters
        areas={mockAreas}
        organisations={mockOrganisations}
      />
    );

    const clearButton = screen.getByRole('button', { name: 'Clear all filters' });
    fireEvent.click(clearButton);

    await waitFor(() => {
      expect(mockRouter.push).toHaveBeenCalledWith('/data');
    });
  });

  it('shows search input for organisations when many options', () => {
    const manyOrgs: FilterOption[] = Array.from({ length: 15 }, (_, i) => ({
      value: `${i}`,
      label: `Operator ${i}`,
    }));

    render(
      <DatasetFilters
        areas={mockAreas}
        organisations={manyOrgs}
      />
    );

    expect(screen.getByPlaceholderText('Search publishers...')).toBeInTheDocument();
  });

  it('filters organisations by search term', () => {
    const manyOrgs: FilterOption[] = [
      { value: '1', label: 'Arriva' },
      { value: '2', label: 'First Bus' },
      { value: '3', label: 'Stagecoach' },
      { value: '4', label: 'Go Ahead' },
      { value: '5', label: 'National Express' },
      { value: '6', label: 'Transdev' },
      { value: '7', label: 'Lothian Buses' },
      { value: '8', label: 'Reading Buses' },
      { value: '9', label: 'Brighton & Hove' },
      { value: '10', label: 'TfL' },
      { value: '11', label: 'Metrobus' },
    ];

    render(
      <DatasetFilters
        areas={mockAreas}
        organisations={manyOrgs}
      />
    );

    const searchInput = screen.getByPlaceholderText('Search publishers...');
    fireEvent.change(searchInput, { target: { value: 'bus' } });

    const orgSelect = screen.getByLabelText('Publisher') as HTMLSelectElement;
    expect(orgSelect.options.length).toBeLessThan(manyOrgs.length + 1);
  });

  it('disables controls when loading', () => {
    render(
      <DatasetFilters
        areas={mockAreas}
        organisations={mockOrganisations}
        isLoading={true}
      />
    );

    expect(screen.getByLabelText('Geographical area')).toBeDisabled();
    expect(screen.getByLabelText('Publisher')).toBeDisabled();
    expect(screen.getByLabelText('Status')).toBeDisabled();
    expect(screen.getByLabelText('Data type')).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Apply filter' })).toBeDisabled();
  });

  it('syncs with URL parameters on mount', () => {
    mockSearchParams.set('area', '2');
    mockSearchParams.set('status', 'inactive');

    render(
      <DatasetFilters
        areas={mockAreas}
        organisations={mockOrganisations}
      />
    );

    const areaSelect = screen.getByLabelText('Geographical area') as HTMLSelectElement;
    expect(areaSelect.value).toBe('2');

    const statusSelect = screen.getByLabelText('Status') as HTMLSelectElement;
    expect(statusSelect.value).toBe('inactive');
  });

  it('resets to page 1 when filter changes', async () => {
    mockSearchParams.set('page', '3');

    render(
      <DatasetFilters
        areas={mockAreas}
        organisations={mockOrganisations}
      />
    );

    const areaSelect = screen.getByLabelText('Geographical area');
    fireEvent.change(areaSelect, { target: { value: '1' } });

    await waitFor(() => {
      expect(mockRouter.push).toHaveBeenCalledWith(
        expect.not.stringContaining('page=')
      );
    });
  });
});
