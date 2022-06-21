class MyAccountMenu {
  myAccount;
  dropdownContent;

  constructor() {
    this.myAccount = document.querySelector(".bods-dropdown");
    this.dropdownContent = document.querySelector(".dropdown-content");

    // only add event listener if "My Account" exists (i.e. when logged in)
    if (this.myAccount) {
      document.addEventListener("click", this.toggleDropdown);
    }
  }

  toggleDropdown = (event) => {
    // don't toggle (open) dropdown if user clicks outside "My Account" area
    // when dropdown is closed
    const shouldToggle =
      this.myAccount.contains(event.target) ||
      this.dropdownContent.classList.contains("open");
    if (shouldToggle) {
      // open if user clicks within the "My Account" area and dropdown not
      // already open, otherwise close dropdown is closed on page load and does
      // not initially have the open class
      const shouldOpen =
        this.myAccount.contains(event.target) &&
        !this.dropdownContent.classList.contains("open");
      const ariaHidden = shouldOpen ? false : true;
      const ariaExpanded = shouldOpen ? true : false;

      this.dropdownContent.classList.toggle("open");
      this.myAccount.classList.toggle("open");
      this.dropdownContent.setAttribute("aria-hidden", ariaHidden);
      this.myAccount.setAttribute("aria-expanded", ariaExpanded);
    }
  };
}

export { MyAccountMenu };
