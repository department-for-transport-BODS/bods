const { merge } = require("webpack-merge");
const common = require("./webpack.common.js");

module.exports = merge(common, {
  mode: "development",
  watch: true,
  devtool: "inline-source-map",
  devServer: {
    allowedHosts: [".bods.local"],
    static: "./frontend/static/frontend",
  },
});
