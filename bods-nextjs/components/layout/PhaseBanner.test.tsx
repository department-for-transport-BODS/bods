import { render, screen } from '@testing-library/react';
import { PhaseBanner } from './PhaseBanner';

jest.mock('next/navigation', () => ({
  usePathname: () => '/changelog',
  useRouter: () => ({ push: jest.fn() }),
}));

describe('PhaseBanner', () => {
  it('links global feedback to the Next.js feedback page', () => {
    render(<PhaseBanner />);

    expect(screen.getByRole('link', { name: 'feedback' })).toHaveAttribute(
      'href',
      '/feedback',
    );
  });
});
