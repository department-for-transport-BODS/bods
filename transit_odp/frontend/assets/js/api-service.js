import { HttpClient } from "./http-client";

class APIService {
  constructor(apiURL, dqsClass) {
    this.dqsClass = dqsClass,
    this.apiURL = apiURL;
    this.httpClient = new HttpClient();
  }

  getDQSReportStatus(revisionId) {
    return this.httpClient
      .get(`${this.apiURL}${this.dqsClass}/${revisionId}/dqs-status/`)
      .then((response) => response.json());
  }
}



export { APIService };
