/**
 * Payload of the public data-host endpoint backing the timetable dataset
 * detail page.
 *
 * API: transit_odp/timetables/views/dataset_detail_api.py
 *      (GET /api/browser/timetables/<id>/ on the data host)
 */

export interface DatasetDetailDataQuality {
  /** true: new DQS report (RAG-less tag); false: legacy score + RAG */
  newDqsReport: boolean;
  reportId: number | null;
  /** New DQS only */
  criticalCount: number | null;
  /** New DQS only; null when the Feedback level is absent from the summary */
  feedbackCount: number | null;
  /** Legacy only, e.g. "95%" */
  score: string | null;
  /** Legacy only: success | warning | error | ... */
  cssIndicator: string | null;
  /** Legacy only, upper case e.g. "AMBER" */
  ragLevel: string | null;
}

export interface DatasetDetailServiceNumberLine {
  lineName: string;
  serviceCodes: string[];
}

export interface DatasetDetailNoc {
  noc: string;
  lines: DatasetDetailServiceNumberLine[];
}

export interface DatasetDetailLicence {
  licenceNumber: string;
  nocs: DatasetDetailNoc[];
}

export interface TimetableDatasetDetail {
  id: number;
  name: string;
  description: string;
  organisationId: number;
  organisationName: string;
  /** live | inactive (the only statuses Django lets the public view) */
  status: string;
  revisionId: number;
  transxchangeVersion: string;
  uploadFileExtension: string;
  /** Pre-formatted "j M Y H:i" in local time */
  lastUpdated: string | null;
  publishedBy: string | null;
  /** The live revision's ETL task failed: Django renders the error panel */
  error: boolean;
  dataQuality: DatasetDetailDataQuality | null;
  isSubscribed: boolean;
  /** Feed API URL with the user's API key; only present when signed in */
  feedApi: string | null;
  serviceNumbers: DatasetDetailLicence[];
}
