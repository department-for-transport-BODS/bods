import { HttpClient } from "./http-client";

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
  console.log("Changing text ");
  console.log(document.getElementById(`row-${rowIndex}`));
  const checkboxSuppress = document.getElementById(
    `checkbox-suppress-${rowIndex}`
  );
  const is_suppressed = checkboxSuppress.checked;

  let suppressText = "Suppress";
  if (is_suppressed) {
    suppressText = "Suppressed";
  }
  console.log(`text: ${suppressText}, ${is_suppressed} `);
  document.getElementById(`row-${rowIndex}`).innerHTML = suppressText;

  console.log(
    `Suppressing observation for ${service_code}, line: ${line_name}`
  );
  // Need to make an AJAX call
  let httpClient = new HttpClient();
  console.log("Calling");
  let hostName = window.location.host;
  hostName = hostName.replace("publish", "data");
  const baseUrl = `${window.location.protocol}//${hostName}/`;
  const apiURL = `${baseUrl}api/app/suppress_observation/suppress/`;
  console.log(`calling the ${apiURL} url`);

  const requestBody = JSON.stringify({
    report_id: report_id,
    revision_id: revision_id,
    organisation_id: organisation_id,
    service_code: service_code,
    line_name: line_name,
    check: observation,
    is_suppressed: is_suppressed,
  });
  let response = httpClient
    .post(`${apiURL}`, requestBody)
    .then((response) => response.json())
    .then((data) => {
      console.log(data);
    })
    .catch((reason) => console.log(reason));
  console.log(response);
}

function suppressAllObservations(
  organisation_id,
  revision_id,
  report_id,
  observation,
  rowIndex
) {
  const checkboxSuppress = document.getElementsByClassName("checkbox-suppress");
  const buttonText = document.getElementById("");

  let suppressText = "Suppress";
  if (is_suppressed) {
    suppressText = "Suppressed";
  }
  console.log(`text: ${suppressText}, ${is_suppressed} `);
  document.getElementById(`row-${rowIndex}`).innerHTML = suppressText;

  console.log(
    `Suppressing observation for ${service_code}, line: ${line_name}`
  );
  // Need to make an AJAX call
  let httpClient = new HttpClient();
  console.log("Calling");
  let hostName = window.location.host;
  hostName = hostName.replace("publish", "data");
  const baseUrl = `${window.location.protocol}//${hostName}/`;
  const apiURL = `${baseUrl}api/app/suppress_observation/suppress/`;
  console.log(`calling the ${apiURL} url`);

  const requestBody = JSON.stringify({
    report_id: report_id,
    revision_id: revision_id,
    organisation_id: organisation_id,
    service_code: service_code,
    line_name: line_name,
    check: observation,
    is_suppressed: is_suppressed,
  });
  let response = httpClient
    .post(`${apiURL}`, requestBody)
    .then((response) => response.json())
    .then((data) => {
      console.log(data);
    })
    .catch((reason) => console.log(reason));
  console.log(response);
}

class APIService {
  constructor(apiURL, dqsClass) {
    (this.dqsClass = dqsClass), (this.apiURL = apiURL);
  }

  getDQSReportStatus(revisionId) {
    return this.httpClient
      .get(`${this.apiURL}${this.dqsClass}/${revisionId}/dqs-status/`)
      .then((response) => response.json());
  }
}

export { APIService };

export { suppressObservation };
