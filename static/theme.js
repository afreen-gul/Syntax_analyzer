// theme.js — W++ Compiler
(function () {
  var html = document.documentElement;
  // Default = dark (original theme)
  var saved = localStorage.getItem('wpp-theme') || 'dark';
  html.setAttribute('data-theme', saved);

  function updateLabel(theme) {
    var lbl = document.getElementById('themeLabel');
    if (lbl) lbl.textContent = theme === 'dark' ? 'DARK' : 'LIGHT';
  }

  updateLabel(saved);

  window.addEventListener('DOMContentLoaded', function () {
    updateLabel(html.getAttribute('data-theme'));
    var btn = document.getElementById('themeToggle');
    if (!btn) return;
    btn.addEventListener('click', function () {
      var cur  = html.getAttribute('data-theme');
      var next = cur === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
      localStorage.setItem('wpp-theme', next);
      updateLabel(next);
    });
  });
})();
