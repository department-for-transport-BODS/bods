import HttpClient from "./http-client";

const INTERVAL_LENGTH = 1000;
const PENDING = "pending";

export class ProgressIndicator {
  constructor(datasetId) {
    this.datasetProgressUrl = `/dataset/${datasetId}/progress/`;
    this.httpClient = new HttpClient();
    this.progressBar = document.getElementById("progressInnerDiv");
    this.progressText = document.getElementById("progressSpan");
    this.interval = null;
    this.previousProgressValue = null;
    // Run get progress once before setting interval (prevents initial load at unknown progress %).
    this.getProgress();
    this.pollProgress();
  }

  pollProgress() {
    this.interval = setInterval(() => this.getProgress(), INTERVAL_LENGTH);
  }

  getProgress() {
    this.httpClient
      .get(this.datasetProgressUrl)
      .then((response) => response.json())
      .then((responseJson) => {
        const progressValue = responseJson["progress"];
        const statusValue = responseJson["status"];
        // An update to the DOM is only required if the progress value is different from previous check.
        if (progressValue !== this.previousProgressValue) {
          this.updateProgressIndicator(progressValue);
        }
        if (progressValue === 100) {
          clearInterval(this.interval);
          if (statusValue !== PENDING) {
            // If progress is 100 and dataset has successfully been uploaded,
            // stop polling and trigger reload
            window.location.reload();
          }
        }
      })
      .catch((error) => {
        clearInterval(this.interval);
        throw new Error(error);
      });
  }

  updateProgressIndicator(progressValue) {
    // Update the progress bar width and label text with percentage completion.
    this.previousProgressValue = progressValue;
    this.progressBar.style.width = `${progressValue}%`;
    this.progressText.innerText = `${progressValue}%`;
  }
}
