/**
 * GDS Provider Component
 *
 * Wraps the application with GDS components provider
 * This ensures GDS components work correctly throughout the app
 *
 * Note: govuk-frontend CSS is loaded via link tag in the layout's head
 * to avoid Next.js CSS processing issues.
 * TODO: Fix this
 */

'use client';

import { ReactNode } from 'react';

interface GDSProviderProps {
  children: ReactNode;
}

export function GDSProvider({ children }: GDSProviderProps) {
  return <>{children}</>;
}

