// Image compression

const gulp = require("gulp");

// Plugins
const imagemin = require("gulp-imagemin");

const paths = PATH_CONFIG;

const imgCompression = () => {
  return gulp
    .src([
      paths.images + "/**",
      paths.node_modules + "/govuk-frontend/govuk/assets/images/**"
    ])
    .pipe(imagemin()) // Compresses PNG, JPEG, GIF and SVG images
    .pipe(gulp.dest(paths.dist + "/images"));
};

module.exports = imgCompression;
