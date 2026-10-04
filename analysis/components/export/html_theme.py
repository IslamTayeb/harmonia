"""Theme-aware HTML helpers for exported Plotly visualizations.

Embeds start in the theme named by ``?theme=`` (light by default) and switch
live when the embedding page posts ``{harmoniaTheme: 'light' | 'dark'}``, so
a theme change never reloads the iframe or re-downloads Plotly. On load the
page posts ``{harmoniaReady: true}`` to its parent so the parent can reply
with its current theme.
"""

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
