import "../sass/project.scss";

const GOVUKFrontend = require("govuk-frontend");

import { CrispyFormsGovUK } from "./crispyforms";
import { APIService } from "./api-service";
import { AutoCompleteSearch } from "./autocomplete";
import { LicenceCheckbox, DisableInputs } from "./disable-inputs";
import { MyAccountMenu } from "./my-account-menu";
import { ProgressIndicator } from "./feed-detail-progress";
import { autoFocusToClass } from "./autofocus";
import { copyToClipboard } from "./copy_to_clipboard";
import { createCookie } from "./cookie_consent";
import { initAPIDocs } from "./api-docs";
import { initDatasetListLoaders } from "./feed-list-progress";
import { initFaresDetailMap } from "./fares-detail-map";
import { initHelpModals } from "./help-modal";
import { initMap } from "./feed-detail-map";
import { initTimeoutWarning } from "./timeout-warning";
import { initWarningDetailMap } from "./data-quality-detail-map";
import { refresh } from "./dqs-review-panel";

function initAll() {
  console.log(`Initialising BODSFrontend -   ${new Date().toISOString()}`);
  initTimeoutWarning();
  initHelpModals();
  GOVUKFrontend.initAll();
}

window.GOVUKFrontend = GOVUKFrontend;
window.CrispyFormsGovUK = CrispyFormsGovUK;

export {
  APIService,
  AutoCompleteSearch,
  DisableInputs,
  LicenceCheckbox,
  MyAccountMenu,
  ProgressIndicator,
  autoFocusToClass,
  copyToClipboard,
  createCookie,
  initAPIDocs,
  initAll,
  initDatasetListLoaders,
  initFaresDetailMap,
  initMap,
  initWarningDetailMap,
  refresh,
};
