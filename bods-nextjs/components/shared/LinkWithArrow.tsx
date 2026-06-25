import Link from 'next/link';
import { ReactNode } from 'react';

interface LinkWithArrowProps {
  href: string;
  children: ReactNode;
  className?: string;
  target?: string;
  rel?: string;
}

export function LinkWithArrow({ href, children, className = 'govuk-link', target, rel }: LinkWithArrowProps) {
  return (
    <Link className={className} href={href} target={target} rel={rel}>
      {children} <span aria-hidden="true">&raquo;</span>
    </Link>
  );
}