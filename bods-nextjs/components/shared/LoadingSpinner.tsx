/**
 * Loading Spinner Component
 *
 * Replace this if we can use a GDS component in future
 * Move the inline css to be in a file
 */

'use client';

interface LoadingSpinnerProps {
  message?: string;
  size?: 'small' | 'medium' | 'large';
  centered?: boolean;
}

export function LoadingSpinner({
  message = 'Loading',
  size = 'medium',
  centered = true,
}: LoadingSpinnerProps) {
  const sizeClasses = {
    small: 'loading-spinner--small',
    medium: 'loading-spinner--medium',
    large: 'loading-spinner--large',
  };

  return (
    <div
      className={`loading-spinner-container ${centered ? 'loading-spinner-container--centered' : ''}`}
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <div className={`loading-spinner ${sizeClasses[size]}`} aria-hidden="true">
        <svg
          className="loading-spinner__svg"
          viewBox="0 0 50 50"
          xmlns="http://www.w3.org/2000/svg"
        >
          <circle
            className="loading-spinner__circle"
            cx="25"
            cy="25"
            r="20"
            fill="none"
            strokeWidth="4"
          />
        </svg>
      </div>
      <span className="govuk-visually-hidden">{message}</span>
      {message && (
        <p className="govuk-body loading-spinner__message" aria-hidden="true">
          {message}
        </p>
      )}

      <style jsx>{`
        .loading-spinner-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1rem;
          padding: 2rem;
        }

        .loading-spinner-container--centered {
          justify-content: center;
          min-height: 200px;
        }

        .loading-spinner {
          display: inline-block;
        }

        .loading-spinner--small {
          width: 24px;
          height: 24px;
        }

        .loading-spinner--medium {
          width: 40px;
          height: 40px;
        }

        .loading-spinner--large {
          width: 60px;
          height: 60px;
        }

        .loading-spinner__svg {
          width: 100%;
          height: 100%;
          animation: rotate 2s linear infinite;
        }

        .loading-spinner__circle {
          stroke: #1d70b8; /* GDS blue */
          stroke-linecap: round;
          animation: dash 1.5s ease-in-out infinite;
        }

        .loading-spinner__message {
          margin: 0;
          color: #505a5f; /* GDS secondary text */
        }

        @keyframes rotate {
          100% {
            transform: rotate(360deg);
          }
        }

        @keyframes dash {
          0% {
            stroke-dasharray: 1, 150;
            stroke-dashoffset: 0;
          }
          50% {
            stroke-dasharray: 90, 150;
            stroke-dashoffset: -35;
          }
          100% {
            stroke-dasharray: 90, 150;
            stroke-dashoffset: -124;
          }
        }
      `}</style>
    </div>
  );
}

