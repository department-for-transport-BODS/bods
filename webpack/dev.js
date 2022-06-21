const { merge } = require("webpack-merge");
const common = require("./common.js");

module.exports = merge(common, {
  mode: "development",
  watch: true,
  devtool: "inline-source-map",
  devServer: {
    allowedHosts: [".bods.local"],
    static: "transit_odp/frontend/static/frontend",
  },
});
