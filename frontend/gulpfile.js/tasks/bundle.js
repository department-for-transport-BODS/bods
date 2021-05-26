"use strict";

// Browserify
const gulp = require("gulp");
const watchify = require("watchify");
const browserify = require("browserify");
const streamify = require("gulp-streamify");
const uglify = require("gulp-uglify");
const source = require("vinyl-source-stream");
const buffer = require("vinyl-buffer");
const log = require("gulplog");
const sourcemaps = require("gulp-sourcemaps");

const paths = PATH_CONFIG;
const jsBundleFile = "bundle.js";

// useful reference: https://gist.github.com/davidbyttow/249c3156de491f999e40

const buildBundle = (obfuscate, watch) => {
  let bundler = browserify({
    entries: [paths.js + "/main.js"],
    standalone: "BODSFrontend",
    debug: false
    // cache: {},
    // packageCache: {},
    // extensions: ['.js', '.json', '.jsx'],
    // paths: [jsSrcDir],
    // fullPaths: false
  });

  // TODO - need to see the correct way to handle sourcemaps
  bundler = bundler.transform("babelify", {
    presets: [
      [
        "@babel/preset-env",
        {
          useBuiltIns: "entry",
          corejs: 3
        }
      ]
    ],
    plugins: ["@babel/plugin-proposal-class-properties"]
  });

  const bundle = b => {
    let startMs = Date.now();
    let db = b
      .bundle()
      .on("error", err => {
        console.error(err.message);
        this.emit("end");
      })
      .pipe(source(jsBundleFile));
    // .pipe(buffer())
    // .pipe(sourcemaps.init({loadMaps: true}));
    if (obfuscate) {
      db = db.pipe(streamify(uglify()));
    }
    // db = db.pipe(sourcemaps.write('./'))
    db = db.pipe(gulp.dest(paths.dist));
    console.log("Updated bundle file in", Date.now() - startMs + "ms");
    return db;
  };

  if (watch) {
    bundler = watchify(bundler).on("update", () => bundle(bundler));
  }

  return bundle(bundler);
};

const buildJs = () => buildBundle(false, false);
const watchJs = () => buildBundle(false, true);
const releaseJs = () => buildBundle(true, false);

module.exports = {
  buildJs,
  watchJs,
  releaseJs
};
