'use client';

import { ReactNode, useEffect, useId, useState } from 'react';
import { createPortal } from 'react-dom';

interface ModalProps {
  open: boolean;
  title: string;
  children: ReactNode;
  onClose: () => void;
  description?: ReactNode;
  closeLabel?: string;
  showCloseButton?: boolean;
}

export function Modal({
  open,
  title,
  children,
  onClose,
  description,
  closeLabel = 'Close',
  showCloseButton = true,
}: ModalProps) {
  const [mounted, setMounted] = useState(false);
  const titleId = useId();

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!open) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.body.style.overflow = 'hidden';
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.overflow = '';
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [open, onClose]);

  if (!open || !mounted) {
    return null;
  }

  return createPortal(
    <div className="shared-modal" role="presentation" onClick={onClose}>
      <div
        className="shared-modal__dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onClick={(event) => event.stopPropagation()}
      >
        {showCloseButton ? (
          <button
            type="button"
            aria-label={closeLabel}
            className="shared-modal__close govuk-link"
            onClick={onClose}
          >
            {closeLabel}
          </button>
        ) : null}
        <h2 className="govuk-heading-m govuk-!-margin-bottom-2" id={titleId}>
          {title}
        </h2>
        {description ? (
          <div className="govuk-body govuk-!-margin-bottom-4">{description}</div>
        ) : null}
        {children}
      </div>

      <style jsx>{`
        .shared-modal {
          position: fixed;
          inset: 0;
          z-index: 1100;
          background: rgba(11, 12, 12, 0.55);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 1rem;
        }

        .shared-modal__dialog {
          width: 100%;
          max-width: 40rem;
          background: #fff;
          border: 4px solid #0b0c0c;
          padding: 1.5rem;
          position: relative;
          box-shadow: 0 4px 18px rgba(11, 12, 12, 0.2);
        }

        .shared-modal__close {
          position: absolute;
          top: 1rem;
          right: 1rem;
          background: transparent;
          border: 0;
          padding: 0;
          cursor: pointer;
        }
      `}</style>
    </div>,
    document.body,
  );
}