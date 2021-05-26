// Styles autoprefixing and minification

const gulp = require("gulp");

// Plugins
const sass = require("gulp-sass"),
  mergeStream = require("merge-stream"),
  sourcemaps = require("gulp-sourcemaps"),
  autoprefixer = require("gulp-autoprefixer"),
  cssnano = require("gulp-cssnano"),
  concat = require("gulp-concat"),
  rename = require("gulp-rename"),
  plumber = require("gulp-plumber"),
  pixrem = require("gulp-pixrem");

const paths = PATH_CONFIG;

const styles = () => {
  const cssStream = gulp.src([
    paths.node_modules + "/normalize.css/normalize.css",
    paths.node_modules + "/mapbox-gl/dist/mapbox-gl.css",
    paths.node_modules + "/swagger-ui/dist/swagger-ui.css"
  ]);

  const sassStream = gulp
    .src([paths.sass + "/**/*.scss"])
    .pipe(sourcemaps.init())
    .pipe(
      sass({
        includePaths: ["node_modules", paths.sass]
      }).on("error", sass.logError)
    )
    .pipe(sourcemaps.write())
    .pipe(plumber()) // Checks for errors
    .pipe(autoprefixer({ browsers: ["last 2 versions"] })) // Adds vendor prefixes
    .pipe(pixrem()); // add fallbacks for rem units

  // merge the two css streams to bundle them into a single css file
  return mergeStream(cssStream, sassStream)
    .pipe(concat("app.css"))
    .pipe(gulp.dest(paths.dist))
    .pipe(rename({ suffix: ".min" }))
    .pipe(cssnano()) // Minifies the result
    .pipe(gulp.dest(paths.dist));
};

module.exports = styles;
