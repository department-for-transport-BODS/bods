const path = require("path");
const fs = require("fs-extra");
const { sassPlugin } = require("esbuild-sass-plugin");
const esbuild = require("esbuild");

const assetCopies = [
  {
    src: "node_modules/govuk-frontend/dist/govuk/assets/images",
    dest: "transit_odp/frontend/assets/images",
  },
  {
    src: "node_modules/govuk-frontend/dist/govuk/assets/rebrand/images",
    dest: "transit_odp/frontend/assets/images",
  },
  {
    src: "node_modules/govuk-frontend/dist/govuk/assets/fonts",
    dest: "transit_odp/frontend/assets/fonts",
  },
  {
    src: "node_modules/govuk-frontend/dist/govuk/assets/rebrand",
    dest: "transit_odp/frontend/assets/rebrand",
  },
];

async function copyAssets() {
  for (const { src, dest } of assetCopies) {
    await fs.copy(src, dest, { overwrite: true });
    console.log(`Copied ${src} to ${dest}`);
  }
}

async function build({ watch = false } = {}) {
  await copyAssets();

  const outdir = path.resolve(
    process.cwd(),
    "transit_odp",
    "frontend",
    "static",
    "frontend"
  );
  console.log(`Output directory: ${outdir}`);

  const buildOptions = {
    entryPoints: [
      path.resolve(
        process.cwd(),
        "transit_odp",
        "frontend",
        "assets",
        "js",
        "main.js"
      ),
      path.resolve(
        process.cwd(),
        "transit_odp",
        "frontend",
        "assets",
        "sass",
        "project.scss"
      ),
    ],
    bundle: true,
    outdir,
    splitting: true,
    format: "esm",
    globalName: undefined,
    minify: true,
    sourcemap: true,
    loader: {
      ".js": "js",
      ".css": "css",
      ".scss": "css",
      ".png": "file",
      ".jpg": "file",
      ".jpeg": "file",
      ".gif": "file",
      ".svg": "file",
      ".woff": "file",
      ".woff2": "file",
      ".ttf": "file",
      ".otf": "file",
      ".eot": "file",
      ".ico": "file",
    },
    plugins: [
      sassPlugin(),
    ],
    define: {
      "process.env.NODE_ENV": '"production"',
      "Buffer": "buffer",
      "process": JSON.stringify({ browser: true }),
      "global": "window",
    },
    target: ["es2015"],
    logLevel: "info",
    entryNames: "[name].bundle",
    assetNames: "images/[name]-[hash]",
    chunkNames: "chunks/[name]-[hash]",
    metafile: true,
  };

  if (watch) {
    // Use esbuild.context for watch mode
    const ctx = await esbuild.context(buildOptions);
    await ctx.watch();
    console.log("Watching for changes...");
  } else {
    await esbuild.build(buildOptions);
  }
}

// Detect --watch flag
const watch = process.argv.includes("--watch");
build({ watch }).catch(() => process.exit(1));
