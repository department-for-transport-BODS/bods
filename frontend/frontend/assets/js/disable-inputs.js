export class DisableInputs {
  constructor(triggerElementsSelector, toggleDisableElementsSelector) {
    this.triggerElementsSelector = triggerElementsSelector;
    this.toggleDisableElementsSelector = toggleDisableElementsSelector;
    this.setDisablingListener();
    this.onInit();
  }

  onInit() {}

  setDisablingListener() {
    const elements = document.querySelectorAll(this.triggerElementsSelector);
    for (const element of elements) {
      this.disablingListenerHandler(element);
    }
  }

  disablingListenerHandler(triggerElement) {
    triggerElement.addEventListener("change", (event) => {
      this.setDisabled(
        this.toggleDisableElementsSelector,
        event.target.checked
      );
    });
  }

  setDisabled(toggleDisableElementsSelector, checkboxState) {
    const elements = document.querySelectorAll(toggleDisableElementsSelector);
    for (const element of elements) {
      this.disableAttributeHandler(element, checkboxState);
    }
  }

  disableAttributeHandler(toggleDisableElement, checkboxState) {
    if (checkboxState === false) {
      toggleDisableElement.removeAttribute("disabled");
    } else {
      toggleDisableElement.setAttribute("disabled", true);
    }
  }
}

export class LicenceCheckbox extends DisableInputs {
  onInit() {
    this.checkLicenceInputText();
  }

  disablingListenerHandler(triggerElement) {
    triggerElement.addEventListener("input", (event) => {
      // input change e.g. text insert/delete
      if (event.isTrusted) {
        this.checkLicenceInputText();
        return;
      }

      let licenceId = event.data;
      const row = document.getElementById(licenceId);
      const hiddenDelete = document.getElementById(licenceId + "-DELETE");
      const hiddenId = document.getElementById(licenceId + "-id");

      if (!row) {
        return;
      }

      if (hiddenId.value === "") {
        // Javascript created elements
        row.remove();
        hiddenId.remove();
      } else {
        // Django created elements
        row.style.display = "none";
        hiddenDelete.value = "on";
      }
      this.checkLicenceInputText();
    });
  }

  checkLicenceInputText() {
    const licenceInputs = document.querySelectorAll(
      this.triggerElementsSelector
    );
    let hasOccupied = false;
    for (const element of licenceInputs) {
      let hidden = element.parentElement.nextElementSibling.firstElementChild;
      if (hidden.value === "on") {
        continue;
      }
      if (element.value !== "") {
        hasOccupied = true;
        break;
      }
    }
    this.setDisabled(hasOccupied);
  }

  setDisabled(disabledState) {
    const elements = document.querySelectorAll(
      this.toggleDisableElementsSelector
    );
    for (const element of elements) {
      element.disabled = disabledState;
    }
  }
}
