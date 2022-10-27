export function initHelpModals() {
  const helpIcons = document.getElementsByClassName("help-modal");
  for (const el of helpIcons) {
    new HelpModal(el);
  }
}

export class HelpModal {
  constructor(modal) {
    this.modal = modal;
    this.helpIcon = modal.getElementsByClassName("help-icon")[0];
    this.overlay = modal.getElementsByClassName("overlay")[0];
    this.closeButton = this.overlay.getElementsByClassName("close-button")[0];

    this.helpIcon.addEventListener("click", () => {
      this.onOpen();
    });
    this.closeButton.addEventListener("click", () => {
      this.onClose();
    });
  }

  onOpen() {
    document.querySelector("html").classList.add("disable-scroll");
    this.overlay.addEventListener("click", this.onClickAnywhere.bind(this));
    this.overlay.style.display = "flex";
  }

  onClose() {
    document.querySelector("html").classList.remove("disable-scroll");
    this.overlay.style.display = "none";
    this.overlay.removeEventListener("click", this.onClickAnywhere.bind(this));
  }

  onClickAnywhere(event) {
    if (this.overlay.style.display === "flex" && event.target.classList.contains("overlay") && !event.target.classList.contains("window")) {
      this.onClose();
    }
  }
}
