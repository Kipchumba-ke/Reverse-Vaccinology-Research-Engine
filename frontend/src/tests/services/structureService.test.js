import { describe, it, expect, vi, afterEach } from 'vitest'
import { fetchStructure, isUniprotAccession } from '../../services/structureService'

afterEach(() => {
  vi.unstubAllGlobals()
  localStorage.clear()
})

describe('isUniprotAccession', () => {
  it('accepts UniProt accessions in either case', () => {
    expect(isUniprotAccession('P0A911')).toBe(true)
    expect(isUniprotAccession('a0a024r161')).toBe(true)
  })

  it('rejects other identifiers', () => {
    expect(isUniprotAccession('ABC123')).toBe(false)
    expect(isUniprotAccession('WP_000001.1')).toBe(false)
    expect(isUniprotAccession(null)).toBe(false)
  })
})

describe('fetchStructure', () => {
  it('returns the model', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ pdb: 'ATOM' }) }),
    )

    expect(await fetchStructure('P0A911', 't')).toEqual({ pdb: 'ATOM' })
  })

  it('throws the server message on failure', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({ error: 'No model.' }),
      }),
    )

    await expect(fetchStructure('P0A911', 't')).rejects.toThrow('No model.')
  })

  it('treats 401 as an expired session', async () => {
    localStorage.setItem('token', 'old')
    const listener = vi.fn()
    window.addEventListener('auth:expired', listener)
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: false, status: 401, json: async () => ({}) }),
    )

    await expect(fetchStructure('P0A911', 'old')).rejects.toThrow(/session has expired/)
    expect(listener).toHaveBeenCalled()
    expect(localStorage.getItem('token')).toBeNull()

    window.removeEventListener('auth:expired', listener)
  })
})
