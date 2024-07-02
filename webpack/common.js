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
    new MiniCssExtractPlugin({
      filename: "css/[name].css",
    }),
    new webpack.ProvidePlugin({ Buffer: ["buffer", "Buffer"] }),
    new CopyPlugin({
      patterns: [
        { from: "transit_odp/frontend/assets/images", to: "images" },
        {
          from: "node_modules/govuk-frontend/dist/govuk/assets/images",
          to: "images",
        },
      ],
    }),
    new webpack.ProvidePlugin({ process: "process/browser" }),
  ],
  resolve: {
    fallback: {
      punycode: require.resolve("punycode/"),
    },
  },
};
