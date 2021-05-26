export function autoFocusToClass(cssClass) {
  // Function to automatically snap focus to first element in css class
  window.onload = () => {
    document.getElementsByClassName(cssClass)[0].firstElementChild.focus();
  };
}
