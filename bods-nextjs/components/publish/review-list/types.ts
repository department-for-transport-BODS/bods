export type ReviewListKind = 'timetable' | 'avl' | 'fares';

export type ReviewListTab = 'active' | 'draft' | 'archive';

export interface ReviewListColumn {
  key: string;
  label: string;
  orderable: boolean;
  nextSort: string | null;
  direction: 'asc' | 'desc' | null;
  width: string | null;
}

export interface ReviewListRow {
  id: number;
  name: string;
  shortDescription: string;
  status: string | null;
  datasetType: number;
  hasDraftRevision: boolean;
  draftStatus: string | null;
  link: string | null;
  modified: string | null;
  modifiedDisplay: string;
  percentMatching?: string;
  avlFeedLastChecked?: string | null;
  avlFeedLastCheckedDisplay?: string;
}

export interface TimetableBanner {
  servicesRequiringAttention: number;
  applicableServices: number;
  feedbackCount: number;
  seasonalServicesCounter: number;
}

export interface AvlBanner {
  totalConsumerInteractions: number;
  overallPpcScore: number | null;
  isAvlRequireAttentionActive: boolean;
  servicesRequiringAttention: number;
  applicableServices: number;
}

export interface FaresBanner {
  totalConsumerInteractions: number;
  isFaresRequireAttentionActive: boolean;
  servicesRequiringAttention: number;
  applicableServices: number;
}

export type ReviewListBanner = TimetableBanner | AvlBanner | FaresBanner;

export interface ReviewListResponse {
  tab: string;
  pageTitle: string;
  organisation: { id: number; name: string };
  isAgentUser: boolean;
  sort: string;
  columns: ReviewListColumn[];
  page: number;
  pageSize: number;
  totalPages: number;
  count: number;
  hasNext: boolean;
  hasPrevious: boolean;
  banner: ReviewListBanner;
  results: ReviewListRow[];
}
