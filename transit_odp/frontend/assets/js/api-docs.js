const SwaggerUI = require("swagger-ui");

const initAPIDocs = (domId, schemaUrl) => {
  SwaggerUI({
    dom_id: domId,
    url: schemaUrl,
    deepLinking: true,
    presets: [SwaggerUI.presets.apis],
    plugins: [SwaggerUI.plugins.DownloadUrl],
    validatorUrl: null,
    syntaxHighlight: false
  });
};

export { initAPIDocs };
