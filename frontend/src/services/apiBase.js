// Where the API lives.
//
// Empty (the default) means same origin: the app calls relative /api/...
// URLs, which the Vite dev server and the Docker web container forward to
// the API. For a static host such as Netlify, set VITE_API_BASE_URL at build
// time to the API's public address, for example https://api.example.com
const BASE = String(import.meta.env?.VITE_API_BASE_URL ?? '')
  .trim()
  .replace(/\/+$/, '')

export function apiUrl(path) {
  return `${BASE}${path}`
}
