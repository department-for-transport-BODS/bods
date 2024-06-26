#!/usr/bin/env node

import { Command } from 'commander'
import { context, build } from 'esbuild'
import { resolve, join } from 'path'
import { existsSync, cpSync, mkdir } from 'fs'
import { sassPlugin } from 'esbuild-sass-plugin'
import postcss from 'postcss'
import { rimraf } from "rimraf"
import { config } from './esbuild.config.mjs'
import { globSync } from 'glob'

const cli = new Command()
cli.description('ESBuild build cli for Application')
    .option('-s, --source <entry>', 'Source path of files to build')
    .option('-o, --outdir <outdir>', 'Output path of directory to build')
    .option('-w, --watch', 'Watch files', false)
    .option('-d, --debug', 'Debug mode', false)

cli.parse()
const cliArgs = cli.opts()

if (!cliArgs.outdir) {
    console.error('--outdir or -o need pass for outdir to build')
    process.abort(1)
}

const cleanOutputDirPlugin = () => {
    return {
        name: 'cleanOutputDir',
        setup(build) {
            build.onStart(() => {
                const { outdir, outfile } = build.initialOptions;
                if (outdir && existsSync(outdir)) {
                    console.info(`Cleaning ${outdir}`)
                    rimraf.sync(outdir)
                    mkdir(outdir, { recursive: true }, (err) => {
                        if (err) console.error(err);
                    });

                }
                if (outfile && existsSync(outfile)) {
                    console.info(`Cleaning ${outfile}`)
                    rimraf.sync(outfile)
                }

            });
        }
    }
}
const copyStaticFiles = (options = {}) => {
    return {
        name: 'copyStaticFiles',
        setup(build) {
            let src = options.src
            let dest = options.dest
            build.onEnd(() => {
                console.info(`Copying file from "${src}" to "${dest}"`)
                cpSync(src, dest, {
                    dereference: true,
                    errorOnExist: false,
                    force: true,
                    preserveTimestamps: true,
                    recursive: true,
                })
            })
        }
    }
}
const copyFilesFromNodeModule = (options = {}) => {
    return {
        name: 'copyFilesFromNodeModule',
        setup(build) {
            let src = options.src
            let dest = options.dest
            build.onStart(() => {
                console.info(`Copying file from "${src}" to "${dest}"`)
                cpSync(src, dest, {
                    dereference: true,
                    errorOnExist: false,
                    force: true,
                    preserveTimestamps: true,
                    recursive: true,
                })
            })
        }
    }
}


const getEntryPoints = (directoryPath) => {
    console.log(`Reading folder...${directoryPath}`)
    let files=globSync(directoryPath + `**/*.{${config.supportedExtensions}}`, { ignore: 'node_modules/**' });
    files.push(resolve(directoryPath, 'sass/project.scss'))
    return files
}


const esConfig = {
    ...config.esbuildConfig,
    entryPoints: getEntryPoints(cliArgs.source),
    drop: cliArgs.debug ? [] : ['debugger', 'console'],
    sourcemap: cliArgs.debug ? 'both' : 'external',
    outdir: cliArgs.outdir,
    plugins: [
        cleanOutputDirPlugin(),
        copyFilesFromNodeModule({
            src: join(config.node_modules_path, 'govuk-frontend/dist/govuk/assets/fonts'),
            dest: join(cliArgs.source, 'fonts')
        }),
        copyFilesFromNodeModule({
            src: join(config.node_modules_path, 'govuk-frontend/dist/govuk/assets/images'),
            dest: join(cliArgs.source, 'images')
        }),
        sassPlugin({
            sourceMap: true,
            style: 'expanded',
            cssImports: true,
            loadPaths: [config.node_modules_path, resolve(config.__dirname, cliArgs.source)],
            async transform(source, resolveDir) {
                const { css } = await postcss(...config.postcssPlugins).process(source, { from: undefined })
                return css
            }
        }),
        copyStaticFiles({
            src: join(cliArgs.source, 'images'),
            dest: join(cliArgs.outdir, 'images')
        }),

        copyStaticFiles({
            src: join(cliArgs.source, 'fonts'),
            dest: join(cliArgs.outdir, 'fonts')
        }),
    ]
}

if (cliArgs.debug) {
    console.info('Watching...')
    let ctx = await context(esConfig)
    await ctx.watch()
} else {
    console.info("Build started")
    await build(esConfig)
    console.info("Build Complete")
}
