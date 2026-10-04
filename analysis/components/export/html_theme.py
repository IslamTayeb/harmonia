"""HTML helpers that make exported Plotly visualizations light, fast embeds.

Embeds start in the theme named by ``?theme=`` (light by default) and switch
live when the embedding page posts ``{harmoniaTheme: 'light' | 'dark'}``, so
a theme change never reloads the iframe or re-downloads Plotly. On load the
page posts ``{harmoniaReady: true}`` to its parent so the parent can reply
with its current theme.
"""

import base64
import json
import re
from array import array

HARMONIA_THEME_SCRIPT = """
<script id="harmonia-theme-script">
(function () {
  var root = document.documentElement;
  var style = document.createElement('style');
  style.textContent = [
    'html[data-harmonia-theme="dark"],',
    'html[data-harmonia-theme="dark"] body {',
    '  background: transparent !important;',
    '}',
    'html[data-harmonia-theme="dark"] #plotly-div svg text {',
    '  fill: #e8e8e8 !important;',
    '}',
    'html[data-harmonia-theme="dark"] #plotly-div .legend .bg {',
    '  fill: rgba(28, 28, 28, 0.82) !important;',
    '  stroke: rgba(250, 250, 250, 0.28) !important;',
    '}',
    'html[data-harmonia-theme="dark"] #plotly-div .gridlayer path,',
    'html[data-harmonia-theme="dark"] #plotly-div .zerolinelayer path {',
    '  stroke: rgba(250, 250, 250, 0.2) !important;',
    '}'
  ].join('\\n');
  document.head.appendChild(style);

  function setTheme(theme) {
    if (theme === 'dark') {
      root.setAttribute('data-harmonia-theme', 'dark');
    } else {
      root.removeAttribute('data-harmonia-theme');
    }
  }

  setTheme(new URLSearchParams(window.location.search).get('theme'));

  window.addEventListener('message', function (event) {
    var data = event.data;

    if (data && (data.harmoniaTheme === 'dark' || data.harmoniaTheme === 'light')) {
      setTheme(data.harmoniaTheme);
    }
  });

  if (window.parent !== window) {
    window.parent.postMessage({ harmoniaReady: true }, '*');
  }
})();
</script>
"""

THEME_SCRIPT_MARKER = 'id="harmonia-theme-script"'


def with_harmonia_theme_script(html: str) -> str:
    """Inject live light/dark theme support into standalone Plotly HTML exports."""
    if THEME_SCRIPT_MARKER in html:
        return html

    if "</body>" in html:
        return html.replace("</body>", HARMONIA_THEME_SCRIPT + "\n</body>")

    return html + HARMONIA_THEME_SCRIPT


# One plotly.js build holding only the traces these exports draw (built by
# tools/plotly-bundle, 466KB brotli vs 1.4MB for the full build). Every embed
# loads the same commit-pinned, SRI-checked URL, so it downloads once and
# stays in jsDelivr's immutable cache. Rebuild and re-pin when adding a trace.
PLOTLY_BUNDLE_SRC = (
    "https://cdn.jsdelivr.net/gh/IslamTayeb/harmonia@0d3fcdec1e492daa7dd13bc8b8083e43edffabc4"
    "/export/vendor/plotly-harmonia.min.js"
)
PLOTLY_BUNDLE_INTEGRITY = "sha384-8tIDVoAwhi3FHDHwLMuPHrgo34Zn+9lM2PJ85hpH7jhZDH1+5boHkdq5CIwKHqWn"
BUNDLE_TRACES = {"scatter", "bar", "pie", "histogram", "heatmap", "scatter3d"}

_PLOTLY_SCRIPT = re.compile(r'<script charset="utf-8" src="https://cdn[^"]*plotly[^"]*"[^>]*></script>')
_NEW_PLOT = re.compile(r'Plotly\.newPlot\(\s*"[^"]+",\s*')


def _escape_for_script(text: str) -> str:
    return text.replace("<", "\\u003c").replace(">", "\\u003e").replace("/", "\\u002f")


def _downcast_float_arrays(value):
    """Store Plotly's base64 float64 arrays as float32: half the bytes, and
    float32 is far finer than anything an embed can show."""
    if isinstance(value, list):
        for item in value:
            _downcast_float_arrays(item)
    elif isinstance(value, dict):
        if value.get("dtype") == "f8" and isinstance(value.get("bdata"), str):
            floats = array("d", base64.b64decode(value["bdata"]))
            value["bdata"] = base64.b64encode(array("f", floats).tobytes()).decode()
            value["dtype"] = "f4"
        for item in value.values():
            _downcast_float_arrays(item)


def with_partial_plotly_bundle(html: str) -> str:
    """Load the Harmonia-only Plotly bundle and slim the embedded data.

    ``scattergl`` traces are drawn as SVG ``scatter`` so no chart needs the
    WebGL 2D renderer; the exported line charts are small enough for SVG.
    """
    match = _NEW_PLOT.search(html)
    if not match or not _PLOTLY_SCRIPT.search(html):
        return html

    data, end = json.JSONDecoder().raw_decode(html, match.end())
    for trace in data:
        if trace.get("type") == "scattergl":
            trace["type"] = "scatter"
    _downcast_float_arrays(data)
    html = html[: match.end()] + _escape_for_script(
        json.dumps(data, separators=(",", ":"))
    ) + html[end:]

    if not {trace.get("type", "scatter") for trace in data} <= BUNDLE_TRACES:
        return html

    tag = (
        f'<script charset="utf-8" src="{PLOTLY_BUNDLE_SRC}" '
        f'integrity="{PLOTLY_BUNDLE_INTEGRITY}" crossorigin="anonymous"></script>'
    )
    return _PLOTLY_SCRIPT.sub(lambda _: tag, html, count=1)


def finalize_embed_html(html: str) -> str:
    """Apply every embed optimization to a standalone Plotly HTML export."""
    return with_harmonia_theme_script(with_partial_plotly_bundle(html))
