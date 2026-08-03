const fs = require('fs');
const path = require('path');

const src = path.join(__dirname, '..', 'node_modules', 'govuk-frontend', 'dist', 'govuk');
const dest = path.join(__dirname, '..', 'public');

function copyDir(s, d) {
  fs.mkdirSync(d, { recursive: true });
  for (const e of fs.readdirSync(s, { withFileTypes: true })) {
    e.isDirectory() ? copyDir(path.join(s, e.name), path.join(d, e.name)) : fs.copyFileSync(path.join(s, e.name), path.join(d, e.name));
  }
}

fs.mkdirSync(path.join(dest, 'govuk'), { recursive: true });
fs.copyFileSync(path.join(src, 'govuk-frontend.min.css'), path.join(dest, 'govuk', 'govuk-frontend.min.css'));
copyDir(path.join(src, 'assets'), path.join(dest, 'assets'));
