import { resolve } from 'path';
import autoprefixer from 'autoprefixer';
import cssnanoPlugin from 'cssnano';

const __dirname = resolve()
const node_modules_path = resolve(__dirname, 'node_modules')

export const config = {
    __dirname: __dirname,
    supportedExtensions: "js,mjs,ts,tsx,css",
    node_modules_path: node_modules_path,
    postcssPlugins: [
        autoprefixer,
        cssnanoPlugin
    ],
    esbuildConfig: {
        logLevel: 'error',
        charset: 'utf8',
        platform: 'browser',
        mainFields: ['browser', 'main'],
        ignoreAnnotations: false,
        bundle: true,
        legalComments: 'eof',
        minify: true,
        metafile: true,
        keepNames: false,
        color: true,
        target: 'esnext',
        allowOverwrite: true,
        treeShaking: true,
        assetNames: 'assets/[name]-[hash]',
        nodePaths: [node_modules_path],
        loader: {
            '.png': 'file',
            '.jpg': 'file',
            '.gif': 'file',
            '.jpeg': 'file',
            '.svg': 'file',
            '.eot': 'file',
            '.woff2': 'file',
            '.woff': 'file',
            '.ttf': 'file'
        },
    }
};
