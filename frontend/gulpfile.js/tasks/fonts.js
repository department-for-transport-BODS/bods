// Install Fonts

const gulp = require("gulp");

const paths = PATH_CONFIG;

const fonts = () => {
  return gulp
    .src([
      paths.node_modules + "/@fortawesome/fontawesome-free/webfonts/**",
      paths.node_modules + "/govuk-frontend/govuk/assets/fonts/**"
    ])
    .pipe(gulp.dest(paths.dist + "/fonts"));
};

module.exports = fonts;
