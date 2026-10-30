export const SESSION_EXPIRED_EVENT = 'auth:expired'

export const SESSION_EXPIRED_MESSAGE =
  'Your session has expired. Please log in again.'

/**
 * Handle an HTTP 401 from an authenticated API call.
 *
 * Removes the stored token and announces the expiry so the application can
 * return the user to the login page. Returns true when the response was a 401.
 * Do not use this for the login request itself, where 401 means bad credentials.
 */
export function handleUnauthorized(response) {
  if (!response || response.status !== 401) return false

  try {
    localStorage.removeItem('token')
  } catch {
    // Storage can be unavailable; the event below still signals the expiry.
  }

  window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT))
  return true
}
