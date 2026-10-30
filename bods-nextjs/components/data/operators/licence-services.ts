/**
 * Client-side filtering and sorting of the licence services table.
 *
 * Source: transit_odp/frontend/assets/js/licence-details.js
 * (`refreshLicencesList`, `sortLicenceServicesTable`).
 */

import type { LicenceService } from '@/lib/operators';

export interface LicenceFilters {
  /** Checked LTA ids (`blank` is the "Not Assigned" box). */
  ltas: string[];
  inScope: boolean;
  outOfScope: boolean;
  inSeason: boolean;
  outOfSeason: boolean;
  franchises: number[];
  operators: number[];
}

/** The page loads with every LTA/franchise/operator ticked, plus in scope and in season. */
export function initialFilters(
  localAuthorityIds: number[],
  hasNullLocalAuthority: boolean,
  franchiseIds: number[],
  operatorIds: number[],
): LicenceFilters {
  return {
    ltas: [...localAuthorityIds.map(String), ...(hasNullLocalAuthority ? ['blank'] : [])],
    inScope: true,
    outOfScope: false,
    inSeason: true,
    outOfSeason: false,
    franchises: franchiseIds,
    operators: operatorIds,
  };
}

/** Django's `data-local-authority`: the comma separated ids, or `blank` when there are none. */
function serviceLtas(service: LicenceService): string[] {
  const ids = service.localAuthorityIds.trim();
  return ids ? ids.split(',').map((id) => id.trim()) : [];
}

export function matchesFilters(service: LicenceService, filters: LicenceFilters): boolean {
  // With neither box ticked Django treats the group as "everything".
  const scopes = filters.inScope || filters.outOfScope ? filters : { ...filters, inScope: true, outOfScope: true };
  const seasons = filters.inSeason || filters.outOfSeason ? filters : { ...filters, inSeason: true, outOfSeason: true };
  const scopeOk = service.isInScope ? scopes.inScope : scopes.outOfScope;
  const seasonOk = service.isInSeason ? seasons.inSeason : seasons.outOfSeason;

  const ltas = serviceLtas(service);
  const ltaOk =
    filters.ltas.length === 0 || (ltas.length ? ltas : ['blank']).some((lta) => filters.ltas.includes(lta));

  const organisationId = service.licenceOrganisationId;
  const operatorOk =
    (filters.operators.length === 0 && filters.franchises.length === 0) ||
    (organisationId !== null && (filters.operators.includes(organisationId) || filters.franchises.includes(organisationId)));

  return scopeOk && seasonOk && ltaOk && operatorOk;
}

/** Django's `data-service-code`, which `refreshLicencesList` joins (URL-encoded) for the map filter. */
export function mapRegistrationNumber(service: LicenceService): string {
  return `${service.serviceNumber} - ${service.registrationNumber}`;
}

function sortValue(service: LicenceService, column: number): number | string {
  switch (column) {
    case 1:
      return service.requiresAttention ? 1 : 0;
    case 2:
      return service.avlRequiresAttention ? 1 : 0;
    case 3:
      return service.faresRequiresAttention ? 1 : 0;
    default: {
      const text = service.fullRegistrationNumber.trim().toLowerCase();
      return text !== '' && !Number.isNaN(Number(text)) ? parseFloat(text) : text;
    }
  }
}

export function sortServices(services: LicenceService[], column: number, ascending: boolean): LicenceService[] {
  return [...services].sort((a, b) => {
    const aValue = sortValue(a, column);
    const bValue = sortValue(b, column);
    if (aValue < bValue) return ascending ? -1 : 1;
    if (aValue > bValue) return ascending ? 1 : -1;
    return 0;
  });
}
