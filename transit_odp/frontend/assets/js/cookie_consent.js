const cookieExpiry = 0.5; // half a year, 6 months

const _createCookie = (name, domain, value, days) => {
  let expires = "";
  if (days) {
    let date = new Date();
    date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
    expires = date.toGMTString();
  }

  // Modify the domain to ensure cookie functionality can be tested on localhost, as well as ensuring
  // it works across all subdomains in production.
  const domainPart = (domain) && (domain !== "localhost") ? `; domain=.${domain}` : "";
  document.cookie = `${name}=${value}; expires=${expires}; path=/${domainPart}`;
};

const _hideBanner = (elemId) => {
  document.getElementById(elemId).style.display = "none";
};

const _showElement = (elemId) => {
  document.getElementById(elemId).style.display = "block";
};

const acceptCookies = (bannerId, domain) => {
  _createCookie("cookie_msg_ack", domain, "1", cookieExpiry * 365);
  _createCookie("cookie_policy", domain, "accept", cookieExpiry * 365);
  _hideBanner(bannerId);
  _showElement("CookielawBannerAccepted");
};

const rejectCookies = (bannerId, domain) => {
  _createCookie("cookie_msg_ack", domain, "1", cookieExpiry * 365);
  _createCookie("cookie_policy", domain, "reject", cookieExpiry * 365);
  _hideBanner(bannerId);
  _showElement("CookielawBannerRejected");
};

const hideCookieMessage = (elemId) => {
  _hideBanner(elemId);
}

const skipToMain = () => {
  const mainContent = document.getElementById("main-content");
  mainContent.setAttribute("tabindex", "0");
  mainContent.focus();
};

export { skipToMain, acceptCookies, rejectCookies, hideCookieMessage, _createCookie, _hideBanner };
