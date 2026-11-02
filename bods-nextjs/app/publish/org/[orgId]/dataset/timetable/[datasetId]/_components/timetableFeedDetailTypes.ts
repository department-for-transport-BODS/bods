// Response shape of transit_odp/publish/views/timetable_feed_detail_api.py
// (get_timetables_feed_detail_api).

export interface TimetableFeedDataQuality {
  reportId: number | null;
  isNewService: boolean;
  hasCriticalIssues: boolean | null;
  rag: { score: string; ragLevel: string; cssIndicator: string } | null;
}

/** licence number -> NOC -> line name -> service codes */
export type TimetableDistinctAttributes = Record<string, Record<string, Record<string, string[]>>>;

export interface TimetableFeedDetail {
  orgId: number;
  datasetId: number;
  liveRevisionId: number;
  name: string;
  description: string;
  shortDescription: string;
  ownerName: string;
  urlLink: string | null;
  transxchangeVersion: string | null;
  /** Picks the Django template branch: the success page or the error panel. */
  status: 'success' | 'error';
  datasetStatus: string;
  publishedAt: string | null;
  publishedAtDisplay: string;
  publishedBy: string | null;
  severeErrors: string[];
  dataQuality: TimetableFeedDataQuality;
  showPti: boolean;
  hasPtiViolations: boolean;
  distinctAttributes: TimetableDistinctAttributes;
}
