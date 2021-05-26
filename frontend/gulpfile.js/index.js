////////////////////////////////
//Setup//
////////////////////////////////

var gulp = require("gulp");
const requireDir = require("require-dir");

// Relative paths function
const pathsConfig = appName => {
  this.app = "frontend";
  this.assets = this.app + "/assets";
  const vendorsRoot = "node_modules/";

  return {
    app: this.app,
    assets: this.assets,
    dist: this.app + "/static/frontend",
    node_modules: vendorsRoot,

    templates: this.assets + "/templates",
    css: this.assets + "/css",
    sass: this.assets + "/sass",
    fonts: this.assets + "/fonts",
    images: this.assets + "/images",
    js: this.assets + "/js"
  };
};

// Globally expose config objects
global.PATH_CONFIG = pathsConfig();

// Require all tasks in gulpfile.js/tasks, including subfolders
const tasks = requireDir("./tasks", { recurse: true });
console.log(
  "Gulp registered tasks:",
  Object.keys(tasks)
    .sort()
    .join(", ")
);

////////////////////////////////
//Tasks//
////////////////////////////////
// TODO - add test coverage
// TODO - add linting and static analysis tools to JS

// TODO - Refactor inlineJS out of browse/feed_details.html

const common = gulp.parallel(tasks.styles, tasks.imgCompression, tasks.fonts);

const build = gulp.series(
  tasks.clean,
  gulp.parallel(common, tasks.bundle.buildJs)
);

const watch = gulp.series(tasks.clean, gulp.parallel(common, tasks.watch));

exports.build = build;
exports.watch = watch;
exports.clean = tasks.clean;
exports.default = watch;
