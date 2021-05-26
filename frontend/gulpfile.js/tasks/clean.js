const del = require("del");

const paths = PATH_CONFIG;

const clean = () => {
  return del(paths.dist);
};

module.exports = clean;
