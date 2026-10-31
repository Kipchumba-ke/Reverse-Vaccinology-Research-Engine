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

// Read a JSON reply. If the server sent something else (for example an HTML
// error page because the API is not running or not reachable), say so in plain
// words instead of surfacing "Unexpected token '<' ... is not valid JSON".
export async function readJson(response) {
  try {
    return await response.json()
  } catch {
    const status = response?.status ? ` (status ${response.status})` : ''

    throw new Error(
      `The server did not send a valid reply${status}. ` +
        'The ReverseVax API may be offline or not set up for this site.',
    )
  }
}
