"""HTML helpers that make exported Plotly visualizations light, fast embeds.

Embeds start in the theme named by ``?theme=`` (light by default) and switch
live when the embedding page posts ``{harmoniaTheme: 'light' | 'dark'}``, so
a theme change never reloads the iframe or re-downloads Plotly. On load the
page posts ``{harmoniaReady: true}`` to its parent so the parent can reply
with its current theme.
"""

import json
import re

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


# Plotly's partial bundles are ~3x smaller than the full 4.8MB build. Every
# export needs only one of these: 2D charts use the cartesian bundle, 3D
# embeddings use gl3d. Pinned and SRI-checked on jsDelivr (immutable cache).
PLOTLY_BUNDLES = {
    "cartesian": (
        "https://cdn.jsdelivr.net/npm/plotly.js-cartesian-dist-min@3.3.0/plotly-cartesian.min.js",
        "sha384-2CO28T33GZOc/JFyswEziubu7UklcWP0CMkMmeOH9d4yKfaB5AfU5iYs2ipINg6Y",
    ),
    "gl3d": (
        "https://cdn.jsdelivr.net/npm/plotly.js-gl3d-dist-min@3.3.0/plotly-gl3d.min.js",
        "sha384-ZESRdauh2iiQrGcePkNX7WpBfllbdN7Dlvoq9dbvEIf9yiGLUsELlirIlGju0vRm",
    ),
}
CARTESIAN_TRACES = {"scatter", "bar", "pie", "histogram", "heatmap"}
GL3D_TRACES = {"scatter3d"}

_PLOTLY_SCRIPT = re.compile(r'<script charset="utf-8" src="https://cdn[^"]*plotly[^"]*"[^>]*></script>')
_NEW_PLOT = re.compile(r'Plotly\.newPlot\(\s*"[^"]+",\s*')


def _escape_for_script(text: str) -> str:
    return text.replace("<", "\\u003c").replace(">", "\\u003e").replace("/", "\\u002f")


def with_partial_plotly_bundle(html: str) -> str:
    """Load the smallest Plotly bundle that can draw this export's traces.

    ``scattergl`` traces are drawn as SVG ``scatter`` so 2D charts never need
    the WebGL bundle; the exported line charts are small enough for SVG.
    """
    match = _NEW_PLOT.search(html)
    if not match or not _PLOTLY_SCRIPT.search(html):
        return html

    data, end = json.JSONDecoder().raw_decode(html, match.end())
    for trace in data:
        if trace.get("type") == "scattergl":
            trace["type"] = "scatter"
    html = html[: match.end()] + _escape_for_script(
        json.dumps(data, separators=(",", ":"))
    ) + html[end:]

    types = {trace.get("type", "scatter") for trace in data}
    if types <= CARTESIAN_TRACES:
        bundle = "cartesian"
    elif types <= GL3D_TRACES:
        bundle = "gl3d"
    else:
        return html

    src, integrity = PLOTLY_BUNDLES[bundle]
    tag = f'<script charset="utf-8" src="{src}" integrity="{integrity}" crossorigin="anonymous"></script>'
    return _PLOTLY_SCRIPT.sub(lambda _: tag, html, count=1)


def finalize_embed_html(html: str) -> str:
    """Apply every embed optimization to a standalone Plotly HTML export."""
    return with_harmonia_theme_script(with_partial_plotly_bundle(html))
