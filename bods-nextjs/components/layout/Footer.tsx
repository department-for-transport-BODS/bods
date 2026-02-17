/**
 * Footer Component
 * 
 * Uses GDS Footer component from kainossoftwareltd-govuk-react-kainos
 */

'use client';

import dynamic from 'next/dynamic';
const GDSFooter = dynamic(
  () => import('kainossoftwareltd-govuk-react-kainos').then((mod) => mod.Footer),
  { ssr: false }
);

const footerLinks = [
  { href: '/accessibility', text: 'Accessibility' },
  { href: '/privacy-policy', text: 'Privacy Policy' },
  { href: '/cookie', text: 'Cookies' },
  { href: '/contact', text: 'Contact'},
];

export function Footer() {
  return <GDSFooter items={footerLinks} />;
}

