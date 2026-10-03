import { describe, expect, it, vi } from 'vitest'
import { getAnalysisStatus } from '../../services/analysisService'

describe('getAnalysisStatus', () => {
  it('gets the status of an analysis', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        analysis_id: '123',
        status: 'running',
      }),
    })

    globalThis.fetch = fetchMock

    const result = await getAnalysisStatus('123')

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/analyses/123',
    )

    expect(result).toEqual({
      analysis_id: '123',
      status: 'running',
    })
  })

  it('returns the analysis report when the analysis is completed', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        analysis_id: '123',
        status: 'completed',
        report: {
          sequence: 'MKT',
          length: 3,
        },
      }),
    })

    globalThis.fetch = fetchMock

    const result = await getAnalysisStatus('123')

    expect(result).toEqual({
      analysis_id: '123',
      status: 'completed',
      report: {
        sequence: 'MKT',
        length: 3,
      },
    })
  })
})