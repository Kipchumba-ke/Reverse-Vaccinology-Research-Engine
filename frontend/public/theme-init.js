// Apply the saved theme before first paint (light is the default).
// This is a separate file so the Content-Security-Policy can forbid inline scripts.
try {
  var t = localStorage.getItem('theme');
  document.documentElement.setAttribute('data-theme', t === 'dark' ? 'dark' : 'light');
} catch (e) {
  document.documentElement.setAttribute('data-theme', 'light');
}
