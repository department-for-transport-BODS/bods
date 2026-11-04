'use client';

// Django `ButtonHolder(CONTINUE_BUTTON, CANCEL_PUBLISH_BUTTON)`.
export function FormButtons({ isSubmitting = false, onCancel }: Readonly<{ isSubmitting?: boolean; onCancel: () => void }>) {
  return (
    <div className="button-holder">
      <button type="submit" name="submit" value="submit" className="govuk-button" disabled={isSubmitting}>
        Continue
      </button>
      <button type="button" name="cancel" value="cancel" className="govuk-button govuk-button--secondary" onClick={onCancel}>
        Cancel
      </button>
    </div>
  );
}
