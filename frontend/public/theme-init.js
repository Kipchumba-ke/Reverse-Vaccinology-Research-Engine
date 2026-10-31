// Apply the saved theme before first paint (dark is the default).
// This is a separate file so the Content-Security-Policy can forbid inline scripts.
try {
  var t = localStorage.getItem('theme');
  document.documentElement.setAttribute('data-theme', t === 'light' ? 'light' : 'dark');
} catch (e) {
  document.documentElement.setAttribute('data-theme', 'dark');
}
