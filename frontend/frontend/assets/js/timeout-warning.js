import HttpClient from "./http-client";

export function initTimeoutWarning() {
  const dialogs = document.querySelectorAll('[data-module="timeout-warning"]');
  dialogs.forEach((dialog) => {
    new TimeoutWarning(dialog);
  });
}

/**
 * Display a timeout modal when the user's session cookie is going to expire.
 * Countdown timer reset only on user-triggered refresh endpoint call.
 */
export class TimeoutWarning {
  defaultCountdownMinutes = 30 * 60;
  countdownMinutes;
  countdownWindow = 60;
  cancelButton;
  refreshButton;
  httpClient = new HttpClient();
  refreshSessionEndpoint = "/";
  timers = [];
  message;
  messageInterval;

  constructor(dialog) {
    this.dialog = dialog;
    this.countdownMinutes =
      dialog.getAttribute("data-timeout") || this.defaultCountdownMinutes;
    this.countdownWindow =
      dialog.getAttribute("data-timeout-window") || this.countdownWindow;
    this.cancelButton = dialog.querySelector(".dialog-cancel");
    this.cancelButton.addEventListener("click", () => {
      this.closeDialog();
    });
    this.refreshButton = dialog.querySelector(".dialog-refresh");
    this.refreshButton.addEventListener("click", () => {
      this.onRefreshButton();
    });
    this.message = dialog.querySelector(".govuk-body");
    this.setTimers();
  }

  openDialog() {
    let counter = this.countdownWindow;
    this.messageInterval = setInterval(() => {
      this.message.textContent = `Your session will expire in ${counter} seconds. Click Refresh session for more time.`;
      counter--;
    }, 1000);

    document.querySelector("body").classList.add("disable-scroll");
    document.querySelector("#dialog-overlay").style.display = "block";
    this.dialog.style.display = "block";
  }

  onRefreshButton() {
    this.httpClient.get(this.refreshSessionEndpoint).then(() => {
      this.timers.forEach((timer) => {
        clearTimeout(timer);
      });
      this.setTimers();
      clearInterval(this.messageInterval);
      this.closeDialog();
    });
  }

  closeDialog() {
    document.querySelector("body").classList.remove("disable-scroll");
    document.querySelector("#dialog-overlay").style.display = "none";
    this.dialog.style.display = "none";
  }

  setTimers() {
    this.timers = [
      setTimeout(
        () => this.openDialog(),
        (this.countdownMinutes - this.countdownWindow) * 1000
      ),
      setTimeout(() => window.location.reload(), this.countdownMinutes * 1000),
    ];
  }
}
