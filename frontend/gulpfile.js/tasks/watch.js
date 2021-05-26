// Watch

const gulp = require("gulp");
const styles = require("./styles");
const imgCompression = require("./imgCompression");
const bundle = require("./bundle");

const paths = PATH_CONFIG;

const watch = () => {
  gulp.watch([paths.sass + "/**/*.scss"], styles);
  gulp.watch([paths.images + "/**"], imgCompression);
  return bundle.watchJs();
};

module.exports = watch;
