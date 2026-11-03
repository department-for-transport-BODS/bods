import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { HelpModal } from './HelpModal';

describe('HelpModal', () => {
  it('keeps the overlay closed until the icon is activated, and Close hides it again', async () => {
    const { container } = render(
      <HelpModal heading="Compliance of fares data">
        <p>Body copy</p>
      </HelpModal>,
    );
    const overlay = container.querySelector('.overlay');

    expect(overlay).not.toHaveClass('active');
    expect(screen.getByRole('heading', { name: 'Compliance of fares data' })).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Help' }));
    expect(overlay).toHaveClass('active');

    await userEvent.click(screen.getByRole('button', { name: 'Close' }));
    expect(overlay).not.toHaveClass('active');
  });

  it('supports a custom trigger icon', async () => {
    const { container } = render(
      <HelpModal heading="Licence colour" icon={<span data-testid="dot" />}>
        <p>Body</p>
      </HelpModal>,
    );

    await userEvent.click(screen.getByTestId('dot'));
    expect(container.querySelector('.overlay')).toHaveClass('active');
  });
});
