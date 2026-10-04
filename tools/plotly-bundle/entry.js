'use strict';

// Keep in sync with BUNDLE_TRACES in analysis/components/export/html_theme.py.
// scatter ships with the core.
var Plotly = require('plotly.js/lib/core');

Plotly.register([
    require('plotly.js/lib/bar'),
    require('plotly.js/lib/pie'),
    require('plotly.js/lib/histogram'),
    require('plotly.js/lib/heatmap'),
    require('plotly.js/lib/scatter3d'),
]);

module.exports = Plotly;
