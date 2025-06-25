const path = require("path");
const webpack = require("webpack");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const CopyPlugin = require("copy-webpack-plugin");

module.exports = {
  entry: {
    main: path.resolve(
      process.cwd(),
      "transit_odp",
      "frontend",
      "assets",
      "js",
      "main.js"
    ),
  },
  output: {
    library: "BODSFrontend",
    libraryTarget: "umd",
    filename: "[name].bundle.js",
    path: path.resolve(
      process.cwd(),
      "transit_odp",
      "frontend",
      "static",
      "frontend"
    ),
    chunkFilename: "[name].js",
    clean: true,
  },
  optimization: {
    splitChunks: {
      cacheGroups: {
        vendors: {
          test: /[\\/]node_modules[\\/]/,
          name: "vendor",
          chunks: "all",
        },
      },
    },
  },
  module: {
    rules: [
      {
        test: /\.m?js$/,
        exclude: /(node_modules|bower_components)/,
        use: {
          loader: "babel-loader",
          options: {
            sourceMap: true,
            presets: ["@babel/preset-env"],
          },
        },
      },
      {
        test: /\.(sa|sc|c)ss$/,
        use: [
          MiniCssExtractPlugin.loader,
          { loader: "css-loader", options: { sourceMap: true } },
          {
            loader: "sass-loader",
            options: { sourceMap: true, sassOptions: { quietDeps: true } },
          },
        ],
      },
      {
        test: /\.(woff|woff2|ttf|otf|eot|svg)(\?.*$|$)/,
        exclude: [/images/], // Resolve SVG conflict
        type: "asset/resource",
        generator: { filename: "fonts/[hash][ext][query]" },
      },
      {
        test: /\.(png|svg|jpg|jpeg|gif|ico)$/i,
        exclude: [/fonts/],
        type: "asset/resource",
        generator: { filename: "images/[hash][ext][query]" },
      },
    ],
  },
  plugins: [
    // Copy assets first
    new CopyPlugin({
      patterns: [
        {
          from: "node_modules/govuk-frontend/dist/govuk/assets/images",
          to: "transit_odp/frontend/assets/images",
        },
        {
          from: "node_modules/govuk-frontend/dist/govuk/assets/rebrand/images",
          to: "transit_odp/frontend/assets/images",
        },
        {
          from: "node_modules/govuk-frontend/dist/govuk/assets/fonts",
          to: "transit_odp/frontend/assets/fonts",
        },
        {
          from: "node_modules/govuk-frontend/dist/govuk/assets/rebrand",
          to: "transit_odp/frontend/assets/rebrand",
        },
        { from: "transit_odp/frontend/assets/images", to: "images" },
        { from: "transit_odp/frontend/assets/fonts", to: "fonts" },
      ],
    }),
    // Then extract CSS
    new MiniCssExtractPlugin({
      filename: "css/[name].css",
    }),
    new webpack.ProvidePlugin({ Buffer: ["buffer", "Buffer"] }),
    new webpack.ProvidePlugin({ process: "process/browser" }),
  ],
  resolve: {
    fallback: {
      punycode: require.resolve("punycode/"),
    },
  },
};
