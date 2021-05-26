// Note in Babel +7.4 @babel/polyfill was deprecated in favour of directly including corejs
// see https://babeljs.io/docs/en/next/babel-polyfill
const corejs = require("core-js/stable");
const regenerator = require("regenerator-runtime/runtime");

// Polyfill Fetch API
const promise = require("promise-polyfill");
const fetch = require("whatwg-fetch");
