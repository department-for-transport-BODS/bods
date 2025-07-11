// import "../sass/project.scss";

import * as GOVUKFrontend from "govuk-frontend";
import jQuery from "jquery";
import { CrispyFormsGovUK } from "./crispyforms";
import { APIService } from "./api-service";
import { AutoCompleteSearch } from "./autocomplete";
import { LicenceCheckbox, DisableInputs } from "./disable-inputs";
import { MyAccountMenu } from "./my-account-menu";
import { ProgressIndicator } from "./feed-detail-progress";
import { autoFocusToClass } from "./autofocus";
import { copyToClipboard } from "./copy_to_clipboard";
import { createCookie, skipToMain } from "./cookie_consent";
import { initAPIDocs } from "./api-docs";
import { initDatasetListLoaders } from "./feed-list-progress";
import { initFaresDetailMap } from "./fares-detail-map";
import { initHelpModals } from "./help-modal";
import { initMap, fetchAvlLiveLocation } from "./feed-detail-map";
import { initOrgMap } from "./organisation-detail-map";
import { initTimeoutWarning } from "./timeout-warning";
import { initWarningDetailMap } from "./data-quality-detail-map";
import { refresh } from "./dqs-review-panel";
import { CounterCharactersInTextBox } from "./counter-characters-text-box";
import { FormSet } from "./django-formset";
import { initDatePicker, changeTargetDate } from "./timetable";
import { showTooltip, hideTooltip, disableClick } from "./tooltip";
import {
  suppressObservation,
  suppressAllObservations,
  setButtonStatus,
} from "./suppress-observation";

function initAll() {
  console.log(`Initialising BODSFrontend -   ${new Date().toISOString()}`);
  initTimeoutWarning();
  initHelpModals();
  GOVUKFrontend.initAll();
}

window.GOVUKFrontend = GOVUKFrontend;
window.CrispyFormsGovUK = CrispyFormsGovUK;
window.jQuery = jQuery;
window.$ = jQuery;

window.BODSFrontend = {
  jQuery,
  APIService,
  AutoCompleteSearch,
  CounterCharactersInTextBox,
  DisableInputs,
  LicenceCheckbox,
  MyAccountMenu,
  ProgressIndicator,
  autoFocusToClass,
  copyToClipboard,
  createCookie,
  skipToMain,
  initAPIDocs,
  initAll,
  initDatasetListLoaders,
  initFaresDetailMap,
  initMap,
  initOrgMap,
  initWarningDetailMap,
  refresh,
  initDatePicker,
  changeTargetDate,
  showTooltip,
  hideTooltip,
  disableClick,
  FormSet,
  suppressObservation,
  suppressAllObservations,
  setButtonStatus,
  fetchAvlLiveLocation
};
