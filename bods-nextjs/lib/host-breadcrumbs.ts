import { HOSTS } from '@/config/client';
import type { BreadcrumbItem } from '@/components/shared/Breadcrumbs';
import type { BodsSubdomain } from '@/config/hosts';

export function serviceHomeName(area: BodsSubdomain): string {
  switch (area) {
    case 'publish':
      return 'Publish Bus Open Data';
    case 'data':
      return 'Find Bus Open Data';
    case 'admin':
      return 'BODS admin home';
    case 'www':
      return 'Bus Open Data Service';
    default: {
      const exhaustive: never = area;
      return exhaustive;
    }
  }
}

/**
 * Standard BODS breadcrumb prefix: www home, then the current host home
 * (skipped on www so the first crumb is not duplicated).
 */
export function hostBreadcrumbs(
  area: BodsSubdomain,
  ...rest: BreadcrumbItem[]
): BreadcrumbItem[] {
  const items: BreadcrumbItem[] = [
    { label: 'Bus Open Data Service', href: HOSTS.www },
  ];

  if (area !== 'www') {
    items.push({ label: serviceHomeName(area), href: HOSTS[area] });
  }

  return [...items, ...rest];
}
