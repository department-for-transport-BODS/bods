import { render, screen } from '@testing-library/react';
import { HostProvider } from '@/lib/bods-host-context';
import { rememberVerificationEmail } from '@/lib/auth/verification-email';
import { VerificationSentContent } from './VerificationSentContent';

function renderContent() {
  return render(
    <HostProvider hostname="data.example.com">
      <VerificationSentContent />
    </HostProvider>,
  );
}

describe('Verification sent content', () => {
  beforeEach(() => {
    window.sessionStorage.clear();
  });

  it('names the address the verification email went to', () => {
    rememberVerificationEmail('consumer@example.com');

    renderContent();

    expect(
      screen.getByText(/We have sent an email to consumer@example.com to verify your address/),
    ).toBeInTheDocument();
    expect(
      screen.getByText('If you cannot find the email then look in your spam or junk email folder.'),
    ).toBeInTheDocument();
  });

  it('falls back to a generic message when the address was not stashed', () => {
    renderContent();

    expect(
      screen.getByText(/We have sent an email to your email address to verify your address/),
    ).toBeInTheDocument();
  });
});
