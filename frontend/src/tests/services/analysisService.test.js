import { describe, expect, it, vi } from 'vitest'
import { submitAnalysis } from '../../services/analysisService'

describe('submitAnalysis', () => {
  it('submits a protein sequence to the analysis API', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 202,
      json: async () => ({
        analysis_id: '123',
        status: 'pending',
      }),
    })

    globalThis.fetch = fetchMock

    const result = await submitAnalysis(
      'MKTIIALSYIFCLVFADYKDDDDK',
    )

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/analyses',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
        body: JSON.stringify({
          sequence: 'MKTIIALSYIFCLVFADYKDDDDK',
        }),
      }),
    )

    expect(result).toEqual({
      analysis_id: '123',
      status: 'pending',
    })
  })
})