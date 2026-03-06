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

const _showElement = (elemId, action) => {
  if (action) {
    const msg = document.getElementById("cookie-confirmation-message");
    if (msg) {
      msg.innerHTML = `You've ${action} analytics cookies. You can <a class="govuk-link" href="/cookies/">change your cookie settings</a> at any time.`;
    }
  }
  document.getElementById(elemId).style.display = "block";
};

const _processCookieChoice = (bannerId, domain, policy, action) => {
  _createCookie("cookie_msg_ack", domain, "1", cookieExpiry * 365);
  _createCookie("cookie_policy", domain, policy, cookieExpiry * 365);
  _hideBanner(bannerId);
  _showElement("cookie-banner-confirmation", action);
};

const acceptCookies = (bannerId, domain) => {
  _processCookieChoice(bannerId, domain, "accept", "accepted");
};

const rejectCookies = (bannerId, domain) => {
  _processCookieChoice(bannerId, domain, "reject", "rejected");
};

const hideCookieMessage = (elemId) => {
  _hideBanner(elemId);
};

const skipToMain = () => {
  const mainContent = document.getElementById("main-content");
  mainContent.setAttribute("tabindex", "0");
  mainContent.focus();
};

export { acceptCookies, rejectCookies, hideCookieMessage, skipToMain, _createCookie, _hideBanner };
