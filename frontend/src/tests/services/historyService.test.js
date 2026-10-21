import { afterEach, describe, expect, it, vi } from 'vitest'
import { getAnalysisHistory } from '../../services/historyService'

afterEach(() => {
  vi.unstubAllGlobals()
  localStorage.clear()
})

describe('getAnalysisHistory', () => {
  it('requests analysis history with the authentication token', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ analyses: [{ analysis_id: '123' }] }),
    })

    vi.stubGlobal('fetch', fetchMock)

    const result = await getAnalysisHistory('test-token')

    expect(fetchMock).toHaveBeenCalledWith('/api/analyses', {
      headers: { Authorization: 'Bearer test-token' },
    })
    expect(result).toEqual([{ analysis_id: '123' }])
  })

  it('throws an error when the request fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({ error: 'Server error' }),
      }),
    )

    await expect(getAnalysisHistory('test-token')).rejects.toThrow(
      'Server error',
    )
  })

  it('clears an expired token when the server returns 401', async () => {
    localStorage.setItem('token', 'expired-token')

    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({ error: 'Authentication required' }),
      }),
    )

    await expect(getAnalysisHistory('expired-token')).rejects.toThrow(
      'Your session has expired. Please log in again.',
    )

    expect(localStorage.getItem('token')).toBeNull()
  })
})
