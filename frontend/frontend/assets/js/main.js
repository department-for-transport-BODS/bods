const polyfills = require("./polyfills");
const GOVUKFrontend = require("govuk-frontend");
const CrispyFormsGovUK = require("../../../../crispy-forms-govuk/crispy_forms_govuk/static/js/all.js");
const Cookielaw = require("./cookie_consent");
const initMap = require("./feed-detail-map");
const initFaresDetailMap = require("./fares-detail-map");
const initWarningDetailMap = require("./data-quality-detail-map");
const initAPIDocs = require("./api-docs");
const copyToClipboard = require("./copy_to_clipboard");

const APIService = require("./api-service");
const MyAccountMenu = require("./my-account-menu");
import { autoFocusToClass } from "./autofocus";
import { initTimeoutWarning } from "./timeout-warning";
import { refresh } from "./dqs-review-panel";
import { initDatasetListLoaders } from "./feed-list-progress";
import { ProgressIndicator } from "./feed-detail-progress";

// Expose GOVUKFrontend globally to call init from HTML after linking bundle.
window.GOVUKFrontend = GOVUKFrontend;

// Do something similar with crispy-forms-govuk 'library'
window.CrispyFormsGovUK = CrispyFormsGovUK;

const initAll = (options) => {
  console.log(`Initialising BODSFrontend - ${new Date().toISOString()}`);
  initTimeoutWarning();
  GOVUKFrontend.initAll();

  // const apiUrl = options.apiURL;
  // const apiService = new APIService(apiUrl);

  // const $pqsPanels = document.querySelectorAll('[data-module="app-dqs-panel"]');
  // $pqsPanels.forEach(($panel) => new DQSReviewPanel($panel, apiService));
};

module.exports = {
  Cookielaw: Cookielaw,
  initMap,
  initFaresDetailMap,
  initWarningDetailMap,
  initDatasetListLoaders,
  initAPIDocs,
  copyToClipboard,
  refresh,
  MyAccountMenu,
  autoFocusToClass,
  ProgressIndicator,
  initAll,
};
