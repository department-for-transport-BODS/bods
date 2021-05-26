const jasmine = require("jasmine");
const Cookielaw = require("../../frontend/assets/js/cookie_consent");

describe("Cookie consent", () => {
  beforeEach(() => {
    var fixture = '<div id="bannerId"></div>';
    document.body.insertAdjacentHTML("afterbegin", fixture);
  });

  afterEach(() => {
    document.body.removeChild(document.getElementById("bannerId"));
  });

  it("should create a consent cookie to expire in 10 years", () => {
    // Setup
    const name = "cookielaw_accepted";
    const days = 10 * 365;

    let date = new Date();
    date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
    expires = date.toGMTString();

    const domain = "example.com";

    const expected = `${name}=1; expires=${expires}; path=/; domain=.${domain}`;

    // spy on cookie property
    const cookie = spyOnProperty(document, "cookie", "set");

    // Test
    Cookielaw.createCookie("bannerId", domain);

    // Assert
    // Note - not sure why the cookie isn't available now - but we can use the spy to test it is set
    // expect(document.cookie).toEqual(expected);
    expect(cookie).toHaveBeenCalledWith(expected);
  });

  it("should hide the banner");
});
