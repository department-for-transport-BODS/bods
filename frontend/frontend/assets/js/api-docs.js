const SwaggerUI = require("swagger-ui");

module.exports = (domId, schemaUrl) => {
  SwaggerUI({
    dom_id: domId,
    url: schemaUrl,
    deepLinking: true,
    presets: [SwaggerUI.presets.apis],
    plugins: [SwaggerUI.plugins.DownloadUrl],
    validatorUrl: null
  });
};
