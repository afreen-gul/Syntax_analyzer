// scanner.js — W++ Compiler
(function () {
  var editor    = document.getElementById('codeEditor');
  var lineNums  = document.getElementById('lineNums');
  var editorInfo= document.getElementById('editorInfo');
  var tokenPill = document.getElementById('tokenCountPill');

  if (!editor) return;

  function updateLineNumbers() {
    var lines = editor.value.split('\n').length;
    var html  = '';
    for (var i = 1; i <= lines; i++) html += '<span>' + i + '</span>';
    lineNums.innerHTML = html;
  }

  function updateStatus() {
    var text   = editor.value;
    var pos    = editor.selectionStart;
    var before = text.substring(0, pos);
    var ln     = before.split('\n').length;
    var col    = before.split('\n').pop().length;
    editorInfo.textContent = 'Ln ' + ln + ', Col ' + col + ' · ' + text.length + ' chars';
  }

  function updateTokenPill() {
    var rows = document.querySelectorAll('.token-table tbody tr');
    if (tokenPill) tokenPill.textContent = rows.length + ' tokens';
  }

  function syncScroll() { lineNums.scrollTop = editor.scrollTop; }

  editor.addEventListener('keydown', function (e) {
    if (e.key === 'Tab') {
      e.preventDefault();
      var s = this.selectionStart, end = this.selectionEnd;
      this.value = this.value.substring(0, s) + '    ' + this.value.substring(end);
      this.selectionStart = this.selectionEnd = s + 4;
      updateLineNumbers();
    }
    if (e.key === 'Enter') {
      var s2 = this.selectionStart;
      var line = this.value.substring(0, s2).split('\n').pop();
      var indent = line.match(/^\s*/)[0];
      var self = this;
      setTimeout(function () {
        var p = self.selectionStart;
        self.value = self.value.substring(0, p) + indent + self.value.substring(p);
        self.selectionStart = self.selectionEnd = p + indent.length;
        updateLineNumbers();
      }, 0);
    }
  });

  editor.addEventListener('input',  function () { updateLineNumbers(); updateStatus(); });
  editor.addEventListener('keyup',  updateStatus);
  editor.addEventListener('click',  updateStatus);
  editor.addEventListener('scroll', syncScroll);

  updateLineNumbers();
  updateStatus();
  updateTokenPill();
})();
