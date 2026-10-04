// Builds export/vendor/plotly-harmonia.min.js: one plotly.js bundle holding
// only the traces Harmonia's exports draw (see entry.js). Mirrors plotly.js's
// own esbuild config. Run: npm install && npm run build
const path = require('path');
const esbuild = require('esbuild');
const { environmentPlugin } = require('esbuild-plugin-environment');
const { glsl } = require('esbuild-plugin-glsl');
const InlineCSSPlugin = require('esbuild-plugin-inline-css');

const outfile = path.join(__dirname, '../../export/vendor/plotly-harmonia.min.js');

esbuild
  .build({
    entryPoints: [path.join(__dirname, 'entry.js')],
    outfile,
    format: 'iife',
    globalName: 'Plotly',
    bundle: true,
    minify: true,
    legalComments: 'eof',
    plugins: [InlineCSSPlugin(), glsl({ minify: true }), environmentPlugin({ NODE_DEBUG: false })],
    alias: { stream: 'stream-browserify' },
    define: { global: 'window', 'define.amd': 'false' },
    target: 'es2016',
    logLevel: 'warning',
  })
  .then(() => console.log(`built ${outfile}`));
