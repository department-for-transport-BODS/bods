import { HttpClient } from "./http-client";

class APIService {
  constructor(apiURL) {
    this.apiURL = apiURL;
    this.httpClient = new HttpClient();
  }

  getDQSReportStatus(revisionId) {
    return this.httpClient
      .get(`${this.apiURL}revision/${revisionId}/dqs-status/`)
      .then((response) => response.json());
  }
}

export { APIService };
