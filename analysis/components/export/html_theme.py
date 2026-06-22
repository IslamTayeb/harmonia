"""Theme-aware HTML helpers for exported Plotly visualizations."""

HARMONIA_THEME_SCRIPT = """
<script>
(function () {
  var params = new URLSearchParams(window.location.search);
  var theme = params.get('theme');

  if (theme !== 'dark') {
    return;
  }

  var textColor = '#e8e8e8';
  var mutedStroke = 'rgba(250, 250, 250, 0.2)';
  document.documentElement.setAttribute('data-harmonia-theme', 'dark');

  var style = document.createElement('style');
  style.id = 'harmonia-dark-theme';
  style.textContent = [
    'html[data-harmonia-theme="dark"],',
    'html[data-harmonia-theme="dark"] body {',
    '  background: transparent !important;',
    '}',
    'html[data-harmonia-theme="dark"] #plotly-div .main-svg text,',
    'html[data-harmonia-theme="dark"] #plotly-div .hoverlayer text {',
    '  fill: ' + textColor + ' !important;',
    '  color: ' + textColor + ' !important;',
    '}',
    'html[data-harmonia-theme="dark"] #plotly-div .legend .bg {',
    '  fill: rgba(28, 28, 28, 0.82) !important;',
    '  stroke: rgba(250, 250, 250, 0.28) !important;',
    '}',
    'html[data-harmonia-theme="dark"] #plotly-div .gridlayer path,',
    'html[data-harmonia-theme="dark"] #plotly-div .zerolinelayer path {',
    '  stroke: ' + mutedStroke + ' !important;',
    '}'
  ].join('\\n');
  document.head.appendChild(style);

  function paintPlotlyText() {
    document
      .querySelectorAll('#plotly-div svg text')
      .forEach(function (text) {
        text.style.setProperty('fill', textColor, 'important');
        text.style.setProperty('color', textColor, 'important');
      });
  }

  function bindPlotlyEvents() {
    var plot = document.getElementById('plotly-div');

    if (plot && plot.on) {
      plot.on('plotly_afterplot', paintPlotlyText);
    }

    paintPlotlyText();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bindPlotlyEvents);
  } else {
    bindPlotlyEvents();
  }

  window.addEventListener('load', paintPlotlyText);
  setTimeout(paintPlotlyText, 500);
  setTimeout(paintPlotlyText, 1500);
})();
</script>
"""


def with_harmonia_theme_script(html: str) -> str:
    """Inject dark-mode support into standalone Plotly HTML exports."""
    if "harmonia-dark-theme" in html:
        return html

    if "</body>" in html:
        return html.replace("</body>", HARMONIA_THEME_SCRIPT + "\n</body>")

    return html + HARMONIA_THEME_SCRIPT
