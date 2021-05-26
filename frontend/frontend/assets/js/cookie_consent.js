const _createCookie = (name, domain, value, days) => {
  let expires = "";
  if (days) {
    let date = new Date();
    date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
    expires = date.toGMTString();
  }
  document.cookie = `${name}=${value}; expires=${expires}; path=/; domain=.${domain}`;
};

const _hideBanner = elemId => {
  if (typeof window.jQuery === "function") {
    jQuery(`#${elemId}`).slideUp();
  } else {
    document.getElementById(elemId).style.display = "none";
  }
};

const createCookie = (bannerId, domain) => {
  _createCookie("cookielaw_accepted", domain, "1", 10 * 365);
  _hideBanner(bannerId);
};

const skipToMain = () => {
  const mainContent = document.getElementById("main-content");
  mainContent.setAttribute("tabindex", "0");
  mainContent.focus();
};

module.exports = {
  createCookie,
  skipToMain,
  // TODO - only exporting these functions to be able to test them
  _createCookie,
  _hideBanner
};
