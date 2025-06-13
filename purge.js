import { PurgeCSS } from "purgecss";
import fs from "fs";
import path from "path";
import sass from "sass";
import glob from "glob";

// 1. Find all SCSS files
const scssDir = "./transit_odp/frontend/assets/sass";
const scssFiles = fs.readdirSync(scssDir).filter((f) => f.endsWith(".scss"));

// 1a. Add ignore list (filenames or relative paths)
const ignoreList = ["variables.scss"];

// 2. Compile each SCSS file to CSS
const compiledCssFiles = [];
const allDefinedClasses = new Set();
for (const file of scssFiles) {
  const scssPath = path.join(scssDir, file);
  const cssPath = scssPath.replace(/\.scss$/, ".purge-tmp.css");
  const result = sass.compile(scssPath);
  fs.writeFileSync(cssPath, result.css);
  compiledCssFiles.push({ cssPath, scssPath, file });

  // Collect all class selectors from SCSS file
  const scssContent = fs.readFileSync(scssPath, "utf-8");
  const classRegex = /\.([a-zA-Z0-9_-]+)\b/g;
  let match;
  while ((match = classRegex.exec(scssContent)) !== null) {
    allDefinedClasses.add(match[1]);
  }
}

// 3. Run PurgeCSS on each compiled CSS file
const purgeResults = await Promise.all(
  compiledCssFiles.map(({ cssPath, scssPath, file }) =>
    new PurgeCSS()
      .purge({
        content: [
          "./transit_odp/**/*.js",
          "./transit_odp/**/*.html",
          "./transit_odp/**/*.py",
          "./node_modules/govuk-frontend/**/*.js",
          "./node_modules/govuk-frontend/**/*.scss",
          "./node_modules/govuk-frontend/**/*.css",
          "./node_modules/@fortawesome/fontawesome-free/**/*.js",
          "./node_modules/@fortawesome/fontawesome-free/**/*.scss",
          "./node_modules/@fortawesome/fontawesome-free/**/*.css",
          "./node_modules/normalize.css/*.css",
          "./node_modules/mapbox-gl/dist/*.css",
          "./node_modules/swagger-ui/dist/*.css",
        ],
        css: [cssPath],
        rejected: true,
      })
      .then((resArr) => ({ resArr, scssPath, file }))
  )
);

// 4. For each unused class, find its line number in the SCSS file
function findClassLineNumbers(scssPath, classNames) {
  const lines = fs.readFileSync(scssPath, "utf-8").split("\n");
  const results = [];
  for (const className of classNames) {
    // Match .classname as a whole word, even if nested or with pseudo/selectors
    const regex = new RegExp(`\\.${className}(\\b|[\\s\\.:,{\\[])`);
    let found = false;
    for (let i = 0; i < lines.length; i++) {
      if (regex.test(lines[i])) {
        results.push({ className, line: i + 1 });
        found = true;
        break;
      }
    }
    if (!found) {
      results.push({ className, line: null }); // Not found in file
    }
  }
  return results;
}

// 5. Delete unused classes from each SCSS file, unless ignored
purgeResults.forEach(({ resArr, scssPath, file }) => {
  if (ignoreList.includes(file) || ignoreList.includes(scssPath)) {
    return;
  }
  resArr.forEach((output) => {
    const unused = output.rejected || [];
    if (!unused.length) return;

    let scssContent = fs.readFileSync(scssPath, "utf-8");

    unused.forEach((className) => {
      // Match .classname { ... } including newlines (non-greedy)
      const regex = new RegExp(
        `\\.${className}\\b[^{]*\\{[\\s\\S]*?\\}`,
        "g"
      );
      scssContent = scssContent.replace(regex, "");
    });

    // Write the cleaned content back to the file
    fs.writeFileSync(scssPath, scssContent, "utf-8");
    console.log(`Removed ${unused.length} unused classes from ${scssPath}`);
  });
});

// 6. Find all classes used in HTML files
const htmlFiles = glob.sync("./transit_odp/**/*.html");
const usedClasses = new Set();
const classAttrRegex = /class=["']([^"']+)["']/g;
for (const htmlPath of htmlFiles) {
  const html = fs.readFileSync(htmlPath, "utf-8");
  let match;
  while ((match = classAttrRegex.exec(html)) !== null) {
    match[1].split(/\s+/).forEach((cls) => {
      if (cls) usedClasses.add(cls);
    });
  }
}

// 7. List missing classes (used in HTML but not defined in SCSS)
const missingClasses = Array.from(usedClasses).filter(
  (cls) => !allDefinedClasses.has(cls)
);

console.log("\nClasses used in HTML but NOT defined in any SCSS file:");
if (missingClasses.length) {
  missingClasses.forEach((cls) => console.log(`  ${cls}`));
  console.log(`Total missing classes: ${missingClasses.length}`);
} else {
  console.log("No missing classes found.");
}

// 8. Clean up temporary CSS files
compiledCssFiles.forEach(({ cssPath }) => fs.unlinkSync(cssPath));
