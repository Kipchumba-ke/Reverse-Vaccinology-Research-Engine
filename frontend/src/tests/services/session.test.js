import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  SESSION_EXPIRED_EVENT,
  handleUnauthorized,
} from '../../services/session'
import {
  downloadAnalysisReport,
  getAnalysisStatus,
  submitAnalysis,
} from '../../services/analysisService'
import { getAnalysisHistory } from '../../services/historyService'

afterEach(() => {
  vi.unstubAllGlobals()
  localStorage.clear()
})

function listenForExpiry() {
  const listener = vi.fn()
  window.addEventListener(SESSION_EXPIRED_EVENT, listener)
  return {
    listener,
    stop: () => window.removeEventListener(SESSION_EXPIRED_EVENT, listener),
  }
}

describe('handleUnauthorized', () => {
  it('clears the token and announces expiry on a 401 response', () => {
    localStorage.setItem('token', 'old-token')
    const { listener, stop } = listenForExpiry()

    expect(handleUnauthorized({ status: 401 })).toBe(true)

    expect(localStorage.getItem('token')).toBeNull()
    expect(listener).toHaveBeenCalledTimes(1)
    stop()
  })

  it('ignores responses that are not 401', () => {
    localStorage.setItem('token', 'keep-me')
    const { listener, stop } = listenForExpiry()

    expect(handleUnauthorized({ status: 200 })).toBe(false)
    expect(handleUnauthorized({ status: 500 })).toBe(false)
    expect(handleUnauthorized(undefined)).toBe(false)

    expect(localStorage.getItem('token')).toBe('keep-me')
    expect(listener).not.toHaveBeenCalled()
    stop()
  })
})

describe('services report an expired session', () => {
  it('signals expiry when submitting an analysis returns 401', async () => {
    localStorage.setItem('token', 'old-token')
    const { listener, stop } = listenForExpiry()

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ error: 'Invalid authentication token.' }),
      }),
    )

    await submitAnalysis('MKTAYIAKQRQISFVKSHFSRQ', 'old-token')

    expect(listener).toHaveBeenCalledTimes(1)
    expect(localStorage.getItem('token')).toBeNull()
    stop()
  })

  it('signals expiry when polling the status returns 401', async () => {
    const { listener, stop } = listenForExpiry()

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ error: 'Invalid authentication token.' }),
      }),
    )

    await getAnalysisStatus('abc', 'old-token')

    expect(listener).toHaveBeenCalledTimes(1)
    stop()
  })

  it('signals expiry when downloading a report returns 401', async () => {
    const { listener, stop } = listenForExpiry()

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ error: 'Invalid authentication token.' }),
      }),
    )

    await expect(downloadAnalysisReport('abc', 'old-token')).rejects.toThrow()

    expect(listener).toHaveBeenCalledTimes(1)
    stop()
  })

  it('signals expiry when loading history returns 401', async () => {
    const { listener, stop } = listenForExpiry()

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ error: 'Authentication required.' }),
      }),
    )

    await expect(getAnalysisHistory('old-token')).rejects.toThrow(
      'Your session has expired. Please log in again.',
    )

    expect(listener).toHaveBeenCalledTimes(1)
    stop()
  })
})
