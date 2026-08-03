import { useState, useCallback } from "react";

interface UseFormSubmitReturn {
  isSubmitting: boolean;
  submitError: string | null;
  handleSubmit: (action: () => Promise<void>) => Promise<void>;
  clearError: () => void;
}

export function useFormSubmit(): UseFormSubmitReturn {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleSubmit = useCallback(async (action: () => Promise<void>) => {
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      await action();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Something went wrong. Please try again.";
      setSubmitError(message);
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  const clearError = useCallback(() => setSubmitError(null), []);

  return { isSubmitting, submitError, handleSubmit, clearError };
}
