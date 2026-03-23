/**
 * Core type definitions for BODS Next.js version
 */

export interface User {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  roles?: string[];
  is_staff?: boolean;
  is_superuser?: boolean;
}

export interface AuthToken {
  token: string;
  user: User;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/**
 * Admin Area (geographic region)
 */
export interface AdminArea {
  atco_code: string;
  name: string;
}

/**
 * Locality (more specific geographic area)
 */
export interface Locality {
  gazetteer_id: string;
  name: string;
}

/**
 * Data Quality RAG status
 */
export type DataQualityRag = 'green' | 'amber' | 'red' | 'unavailable';

/**
 * Dataset type enumeration
 */
export type DatasetType = 'TIMETABLE' | 'AVL' | 'FARES';

/**
 * Dataset status
 */
export type DatasetStatus = 'published' | 'live' | 'inactive' | 'expired' | 'error';

/**
 * Dataset from the /api/v1/dataset/ endpoint
 * Based on Django DatasetSerializer
 */
export interface Dataset {
  id: number;
  organisationId: number;
  revisionId: number;
  created: string;
  modified: string;
  operatorName: string;
  noc: string[];
  name: string;
  description: string;
  comment: string;
  status: DatasetStatus;
  url: string;
  extension: string;
  lines: string[];
  firstStartDate: string | null;
  firstEndDate: string | null;
  lastEndDate: string | null;
  adminAreas: AdminArea[];
  localities: Locality[];
  dqScore: string;
  dqRag: DataQualityRag;
  bodsCompliance: boolean | null;
}

/**
 * Simplified dataset for list view
 */
export interface DatasetListItem {
  id: number;
  name: string;
  operatorName: string;
  description: string;
  status: DatasetStatus;
  modified: string;
  dqScore: string;
  dqRag: DataQualityRag;
  dataType?: DatasetType;
}

