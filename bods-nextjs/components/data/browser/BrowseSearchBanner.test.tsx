import { useState } from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowseSearchBanner } from './BrowseSearchBanner';

const NAMES = ['Alpha Buses', 'alpine Coaches', 'Beta Travel'];

function Harness({ onSubmit }: { onSubmit: (value?: string) => void }) {
  const [value, setValue] = useState('');
  return (
    <BrowseSearchBanner
      title="Operator Profiles"
      description="Search for a specific operator"
      placeholder="Enter operator name"
      searchValue={value}
      onSearchChange={setValue}
      onSearchSubmit={onSubmit}
      suggestions={NAMES}
    />
  );
}

describe('BrowseSearchBanner autocomplete', () => {
  it('lists nothing for a single character, then case-insensitive prefix matches', async () => {
    render(<Harness onSubmit={jest.fn()} />);
    const input = screen.getByPlaceholderText('Enter operator name');

    await userEvent.type(input, 'a');
    expect(screen.queryByText('Alpha Buses')).not.toBeInTheDocument();

    await userEvent.type(input, 'L');
    expect(screen.getByText('Alpha Buses')).toBeInTheDocument();
    expect(screen.getByText('alpine Coaches')).toBeInTheDocument();
    expect(screen.queryByText('Beta Travel')).not.toBeInTheDocument();
  });

  it('submits the clicked suggestion', async () => {
    const onSubmit = jest.fn();
    render(<Harness onSubmit={onSubmit} />);

    await userEvent.type(screen.getByPlaceholderText('Enter operator name'), 'be');
    await userEvent.click(screen.getByText('Beta Travel'));

    expect(onSubmit).toHaveBeenCalledWith('Beta Travel');
  });

  it('chooses the highlighted suggestion with the arrow keys and Enter', async () => {
    const onSubmit = jest.fn();
    render(<Harness onSubmit={onSubmit} />);

    await userEvent.type(screen.getByPlaceholderText('Enter operator name'), 'al{ArrowDown}{ArrowDown}{Enter}');

    expect(onSubmit).toHaveBeenCalledWith('alpine Coaches');
  });

  it('closes the list on an outside click', async () => {
    render(<Harness onSubmit={jest.fn()} />);
    await userEvent.type(screen.getByPlaceholderText('Enter operator name'), 'al');
    expect(screen.getByText('Alpha Buses')).toBeInTheDocument();

    await userEvent.click(document.body);
    expect(screen.queryByText('Alpha Buses')).not.toBeInTheDocument();
  });
});
