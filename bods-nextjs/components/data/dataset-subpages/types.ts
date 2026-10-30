/** Payloads of transit_odp/browse/views/dataset_subpages_api.py */

export interface ChangelogDataQuality {
  /** "Not available", "Generating..." or "" - shown instead of a score. */
  text?: string;
  score?: string;
  ragLevel?: string;
  indicator?: string;
}

export interface ChangelogRow {
  revisionId: number;
  comment: string;
  statusLabel: string;
  statusClass: string;
  updatedAt: string;
  showErrors: boolean;
  errors: string[];
  dataQuality?: ChangelogDataQuality;
}

export interface DatasetChangelog {
  datasetId: number;
  datasetType: 'TIMETABLE' | 'AVL' | 'FARES';
  name: string;
  showDataQuality: boolean;
  count: number;
  page: number;
  pageSize: number;
  totalPages: number;
  results: ChangelogRow[];
}

export interface DatasetSubscriptionState {
  datasetId: number;
  datasetType: 'TIMETABLE' | 'AVL' | 'FARES';
  name: string;
  detailPath: string;
  isAuthenticated: boolean;
  isSubscribed: boolean | null;
  /** Success page only. */
  backPath?: string;
  backButtonText?: string;
}

export interface DatasetFeedback {
  datasetId: number;
  datasetType: 'TIMETABLE' | 'AVL' | 'FARES';
  name: string;
  service: string | null;
  lineName: string | null;
  stopName: string | null;
  atcoCode: string | null;
  journeyStartTime: string | null;
  direction: string | null;
  backPath: string;
}
