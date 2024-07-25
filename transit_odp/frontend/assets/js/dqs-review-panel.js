import { APIService } from "./api-service";

const DQTASK_PENDING = "PENDING";

// refresh
export function refresh(apiURL, revisionID, dqsClass) {
  const apiService = new APIService(apiURL, dqsClass);
  setInterval(() => {
    apiService.getDQSReportStatus(revisionID).then((data) => {
      if (data !== DQTASK_PENDING) {
        location.reload();
      }
    });
  }, 10000);
}
