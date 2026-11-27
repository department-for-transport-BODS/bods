import { render, screen } from '@testing-library/react';
import { FileList, LinePropertyTable } from './LinePropertyTable';

const file = { filename: 'a.xml', startDate: '2024-01-01', endDate: null };

describe('FileList', () => {
  it('shows N/A when there are no files', () => {
    render(<FileList files={[]} />);
    expect(screen.getByText('N/A')).toBeInTheDocument();
  });

  it('shows the date range with Django placeholders, then the file name', () => {
    render(<FileList files={[file, { filename: 'b.xml', startDate: null, endDate: '2025-01-01' }]} />);
    expect(screen.getByText(/2024-01-01 - No End Date/)).toBeInTheDocument();
    expect(screen.getByText(/No Start Date - 2025-01-01/)).toBeInTheDocument();
    expect(screen.getByText(/a\.xml/)).toBeInTheDocument();
    expect(screen.getByText(/b\.xml/)).toBeInTheDocument();
  });
});

describe('LinePropertyTable optional rows', () => {
  const flexible = {
    serviceType: 'Flexible',
    serviceCode: 'PD1:1',
    bookingArrangements: 'Call ahead',
    bookingMethods: { phone: '0123', email: null, url: null },
  };

  it('shows every row by default', () => {
    render(<LinePropertyTable line={{ ...flexible, currentValidFiles: [file] }} />);
    expect(screen.getByText('Registration Number')).toBeInTheDocument();
    expect(screen.getByText('Current valid file(s)')).toBeInTheDocument();
    expect(screen.getByText('Booking arrangements')).toBeInTheDocument();
    expect(screen.getByText('Phone - 0123')).toBeInTheDocument();
  });

  it('can drop the registration, valid files and booking rows (licence line page)', () => {
    render(
      <LinePropertyTable
        line={flexible}
        showRegistrationNumber={false}
        showValidFiles={false}
        showBookingDetails={false}
      />,
    );
    expect(screen.getByText('Type of service')).toBeInTheDocument();
    expect(screen.queryByText('Registration Number')).not.toBeInTheDocument();
    expect(screen.queryByText('Current valid file(s)')).not.toBeInTheDocument();
    expect(screen.queryByText('Booking arrangements')).not.toBeInTheDocument();
  });
});
