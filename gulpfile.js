////////////////////////////////
//Setup//
////////////////////////////////

// Plugins
const gulp = require("gulp"),
  pjson = require("./package.json"),
  spawn = require("child_process").spawn,
  proxy = require("http-proxy-middleware"),
  browserSync = require("browser-sync").create(),
  reload = browserSync.reload;

// Relative paths function
const pathsConfig = appName => {
  this.app = "./" + (appName || pjson.name);
  let vendorsRoot = "node_modules/";

  return {
    app: this.app,
    node_modules: vendorsRoot,
    frontend: "frontend/frontend/static",
    templates: this.app + "/**/templates"
  };
};

const paths = pathsConfig();

////////////////////////////////
//Tasks//
////////////////////////////////

// Run django server
const taskRunServer = done => {
  var cmd = spawn("python", ["manage.py", "runserver_plus", "0.0.0.0:8000"], {
    stdio: "inherit"
  });
  cmd.on("close", function(code) {
    console.log("runServer exited with code " + code);
    done(code);
  });
};

// Browser sync server for live reload
const taskStartBrowserSync = done => {
  browserSync.init(
    [paths.frontend + "/css/*.css", paths.templates + "/**/*.html"],
    {
      middleware: [
        function(req, res, next) {
          let target =
            "http://" +
            req.headers.host.replace("bods.local:3000", "bods.local:8000");
          proxy({
            target,
            changeOrigin: true
          })(req, res, next);
        }
      ],
      rewriteRules: [
        {
          match: /bods.local:8000/g,
          fn: function(req, res, match) {
            return "bods.local:3000";
          }
        }
      ]
    }
  );
  done();
};

// Watch
const taskWatch = done => {
  gulp.watch([paths.frontend + "/**/*"], gulp.series(reload));
  gulp.watch(
    [paths.templates + "/**/*.html"],
    { events: "change" },
    gulp.series(reload)
  );
  gulp.watch(
    [paths.app + "/**/*.py"],
    { events: "change" },
    gulp.series(reload)
  );
  done();
};

// Task which runs BrowserSync but not Django
const watch = gulp.parallel(taskStartBrowserSync, taskWatch);

const run = gulp.parallel(taskRunServer, watch);

exports.default = run;
exports.watch = watch;
exports.run = run;
