import Link from 'next/link';
import { ReactNode } from 'react';

interface LinkWithArrowProps {
  href: string;
  children: ReactNode;
  className?: string;
}

export function LinkWithArrow({ href, children, className = 'govuk-link' }: LinkWithArrowProps) {
  return (
    <Link className={className} href={href}>
      {children} <span aria-hidden="true">&raquo;</span>
    </Link>
  );
}