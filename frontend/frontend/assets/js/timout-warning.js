export class TimoutWarning {
  // default session timeout to 30 minutes as is the case in production
  countdown = 30 * 60;
  countdownWindow = 60;
  cancelButton;
  refreshButton;
  overLayClass = "govuk-timeout-warning-overlay";
  httpClient = new XMLHttpRequest();
  refreshSessionEndpoint = "/";
  timers = [];
  message;
  messageInterval;

  constructor(dialog) {
    this.dialog = dialog;
    this.countdown = dialog.getAttribute("data-timeout") || this.countdown;
    this.countdownWindow =
      dialog.getAttribute("data-timeout-window") || this.countdownWindow;
    this.cancelButton = dialog.querySelector(".dialog-cancel");
    this.cancelButton.addEventListener("click", () => {
      this.onCancelButton();
    });
    this.refreshButton = dialog.querySelector(".dialog-refresh");
    this.refreshButton.addEventListener("click", () => {
      this.onRefreshButton();
    });
    this.message = dialog.querySelector(".govuk-body");
    this.setTimers();

    this.httpClient.addEventListener("load", () => {
      // Only close dialog box when we have a successful response from server
      this.timers.forEach(timer => {
        clearTimeout(timer);
      });
      this.setTimers();
      this.closeDialog();
    });
  }

  openDialog() {
    let counter = this.countdownWindow;
    this.messageInterval = setInterval(() => {
      this.message.textContent = `Your session will expire in ${counter} seconds. Click Refresh session for more time.`;
      counter--;
    }, 1000);
    this.dialog.showModal();
  }

  onCancelButton() {
    this.closeDialog();
  }

  onRefreshButton() {
    this.httpClient.open("GET", this.refreshSessionEndpoint);
    this.httpClient.send();
  }

  closeDialog() {
    this.dialog.close();
    document.querySelector("body").classList.remove(this.overLayClass);
    clearInterval(this.messageInterval);
  }

  setTimers() {
    this.timers = [
      setTimeout(
        () => this.openDialog(),
        (this.countdown - this.countdownWindow) * 1000
      ),
      setTimeout(() => window.location.reload(), this.countdown * 1000)
    ];
  }
}

export function initTimeoutWarning() {
  const dialogs = document.querySelectorAll('[data-module="timeout-warning"]');
  dialogs.forEach(dialog => {
    new TimoutWarning(dialog);
  });
}
