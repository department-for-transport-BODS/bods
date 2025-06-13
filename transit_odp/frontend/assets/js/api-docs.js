
import jQuery from "jquery";
window.jQuery = jQuery;
window.$ = jQuery;
import { Buffer } from 'buffer';
window.buffer = Buffer;
const SwaggerUI = require("swagger-ui");

const initAPIDocs = (domId, schemaUrl) => {
  const csrfTokenElement = document.querySelector('input[name="csrfmiddlewaretoken"');
  const csrftoken = csrfTokenElement.value;

  SwaggerUI({
    dom_id: domId,
    url: schemaUrl,
    deepLinking: true,
    presets: [SwaggerUI.presets.apis],
    plugins: [SwaggerUI.plugins.DownloadUrl],
    validatorUrl: null,
    syntaxHighlight: false,
    requestInterceptor: (request) => {
        request.headers['X-CSRFToken'] = csrftoken;
        return request;
    },
  });
};

export { initAPIDocs };
