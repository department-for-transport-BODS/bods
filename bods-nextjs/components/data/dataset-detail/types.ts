/**
 * Payloads of the public data-host endpoints backing the dataset detail pages.
 *
 * API: transit_odp/timetables/views/dataset_detail_api.py
 *      (GET /api/browser/timetables/<id>/ on the data host)
 *      transit_odp/avl/views/dataset_detail_api.py
 *      (GET /api/browser/avl/<id>/)
 *      transit_odp/fares/views/dataset_detail_api.py
 *      (GET /api/browser/fares/<id>/)
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

export interface AvlDatasetDetail {
  id: number;
  name: string;
  description: string;
  organisationId: number;
  organisationName: string;
  /** Any status of a published feed: Django does not narrow AVL by status */
  status: string;
  revisionId: number;
  /** Pre-formatted "j M Y H:i" in local time ("Feed details last updated") */
  lastUpdated: string | null;
  /** Pre-formatted "j M Y H:i" ("Last automated update"); null when never checked */
  lastAutomatedUpdate: string | null;
  /** Live revision metadata schema version; "" when there is no metadata */
  siriVmVersion: string;
  /** Weekly post-publishing-check score such as "85%"; null while pending */
  avlTimetablesMatching: string | null;
  isSubscribed: boolean;
  /** Feed API URL with the user's API key; only present when signed in */
  feedApi: string | null;
}

/** Metadata values exactly as Django's template prints them (e.g. "None"). */
export interface FaresDatasetMetadata {
  schemaVersion: string;
  numOfFareZones: string;
  numOfLines: string;
  numOfSalesOfferPackages: string;
  numOfFareProducts: string;
  numOfUserProfiles: string;
  validFrom: string;
  validTo: string;
}

export interface FaresDatasetDetail {
  id: number;
  name: string;
  description: string;
  organisationId: number;
  organisationName: string;
  /** Any status of a published dataset; `error` renders Django's error panel */
  status: string;
  /** The live revision id (also the fares validation report's revision) */
  revisionId: number;
  transxchangeVersion: string;
  uploadFileExtension: string;
  /** Pre-formatted "j M Y H:i" in local time */
  lastUpdated: string | null;
  publishedBy: string | null;
  /** Django `show_map`: live, inactive or expired */
  showMap: boolean;
  /** Django `is_compliant_error`: true unless the validation result is compliant */
  isCompliantError: boolean;
  /** A validation result exists, so the report can be downloaded */
  showReportLink: boolean;
  metadata: FaresDatasetMetadata;
  isSubscribed: boolean;
  /** Feed API URL with the user's API key; only present when signed in */
  feedApi: string | null;
}
