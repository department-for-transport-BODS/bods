import { APIService } from "./api-service";

const DQTASK_PENDING = "PENDING";

// refresh
export function refresh(apiURL, revisionID) {
  const apiService = new APIService(apiURL);
  setInterval(() => {
    apiService.getDQSReportStatus(revisionID).then((data) => {
      if (data !== DQTASK_PENDING) {
        location.reload();
      }
    });
  }, 10000);
}
