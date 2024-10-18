import { HttpClient } from "./http-client";

function setButtonStatus() {
  const suppressCheckboxes =
    document.getElementsByClassName("checkbox-suppress");

  const suppressButton = document.getElementById("button-suppress-observation");
  let allChecked = true;
  for (let i = 1; i <= suppressCheckboxes.length; i++) {
    const checkBoxSuppress = document.getElementById(`checkbox-suppress-${i}`);
    if (checkBoxSuppress.checked & allChecked) {
      allChecked = true;
    } else {
      allChecked = false;
      break;
    }
  }

  if (allChecked) {
    suppressButton.textContent = "Restore all observations";
  } else {
    suppressButton.textContent = "Suppress all observations";
  }
}

/**
 * Extract the orgnaisation id, revision id and report id from the url.
 * @returns the orgnaisation id, revision id and report id
 */
function extractOrgRevisionAndReportID() {
  // Create a URL object
  const urlObj = new URL(window.location.href);
  // Use URLSearchParams to extract path segments
  const segments = urlObj.pathname.split("/").filter((segment) => segment);

  // Extract organization ID and dataset ID
  const organisation_id = segments[1];
  const revision_id = segments[4];
  const report_id = segments[6];

  return { organisation_id, revision_id, report_id };
}

/**
 * Get the API URL
 * @returns the API URL of the suppress observation
 */
function getAPIUrl() {
  // Remove trailing slash if it exists
  const url = window.location.href.replace(/#.*$/, "").replace(/\/$/, "");
  // Split the URL by slashes, remove the last segment, and join it back
  const segments = url.split("/");
  segments.pop(); // Remove the last segment
  return segments.join("/") + "/" + "suppress-observation/"; // Re-add the trailing slash
}

/**
 * Set the status of the checkbox
 * @param {boolean} is_suppressed - Whether the check box is suppressed
 * @param {int} rowIndex - Row number of the checkbox
 */
function setStatus(is_suppressed, rowIndex) {
  let suppressText = "Suppress";
  if (is_suppressed) {
    suppressText = "Suppressed";
  }
  document.getElementById(`checkbox-suppress-${rowIndex}`).checked =
    is_suppressed;
  document.getElementById(`row-${rowIndex}`).innerHTML = suppressText;
}

/**
 * Suppress the observation for a specific service code and line name
 * @param {int} organisation_id - Organisation id
 * @param {int} revision_id - Revision id for the dataset
 * @param {int} report_id - Report id for the uploaded revision
 * @param {string} service_code - Service code of the service
 * @param {string} line_name - Line name of the service
 * @param {string} observation - Observation check
 * @param {string} rowIndex - Index of the row, starting from 1
 *
 */
function suppressObservation(
  organisation_id,
  revision_id,
  report_id,
  service_code,
  line_name,
  observation,
  rowIndex
) {
  const checkboxSuppress = document.getElementById(
    `checkbox-suppress-${rowIndex}`
  );
  const is_suppressed = checkboxSuppress.checked;

  // Need to make an AJAX call
  const httpClient = new HttpClient();
  const requestBody = JSON.stringify({
    service_code: service_code,
    line_name: line_name,
    check: observation,
    is_suppressed: is_suppressed,
  });

  httpClient
    .post(`${getAPIUrl()}`, requestBody)
    .then((response) => response.json())
    .then((data) => {
      setStatus(is_suppressed, rowIndex);
      setButtonStatus();
    })
    .catch((reason) => console.log(reason));
}

/**
 * Suppress the observations for a check across all service code and line name.
 */
function suppressAllObservations() {
  const httpClient = new HttpClient();
  const suppressButton = document.getElementById("button-suppress-observation");
  const buttonText = suppressButton.textContent.toLowerCase();
  const observation = document
    .getElementById("observation-title")
    .textContent.trim();

  // Restore all observations
  let is_suppressed = true;
  if (buttonText.includes("restore")) {
    is_suppressed = false;
  }

  const requestBody = JSON.stringify({
    check: observation,
    is_suppressed: is_suppressed,
  });

  httpClient
    .post(`${getAPIUrl()}`, requestBody)
    .then((response) => response.json())
    .then((data) => {
      const suppressCheckboxes =
        document.getElementsByClassName("checkbox-suppress");

      for (let i = 1; i <= suppressCheckboxes.length; i++) {
        setStatus(is_suppressed, i);
      }
      setButtonStatus();
    })
    .catch((reason) => console.log(reason));
}

export { suppressObservation, suppressAllObservations, setButtonStatus };
