import { afterEach, describe, expect, it, vi } from 'vitest'

async function loadApiUrl(base) {
  vi.stubEnv('VITE_API_BASE_URL', base)
  vi.resetModules()
  const module = await import('../../services/apiBase')
  return module.apiUrl
}

describe('apiUrl', () => {
  afterEach(() => {
    vi.unstubAllEnvs()
    vi.resetModules()
  })

  it('keeps relative URLs when no base URL is configured', async () => {
    const apiUrl = await loadApiUrl('')

    expect(apiUrl('/api/login')).toBe('/api/login')
  })

  it('prefixes the configured base URL', async () => {
    const apiUrl = await loadApiUrl('https://api.example.com')

    expect(apiUrl('/api/analyses')).toBe('https://api.example.com/api/analyses')
  })

  it('ignores a trailing slash and surrounding spaces in the base URL', async () => {
    const apiUrl = await loadApiUrl('  https://api.example.com/  ')

    expect(apiUrl('/api/login')).toBe('https://api.example.com/api/login')
  })
})
