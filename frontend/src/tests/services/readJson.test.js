import { afterEach, describe, expect, it, vi } from 'vitest'
import { readJson } from '../../services/apiBase'
import { login } from '../../services/authService'

describe('readJson', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('returns the parsed body of a JSON reply', async () => {
    const response = { json: async () => ({ ok: true }) }

    await expect(readJson(response)).resolves.toEqual({ ok: true })
  })

  it('explains an unreadable reply instead of showing a JSON parse error', async () => {
    const response = {
      status: 404,
      json: async () => {
        throw new SyntaxError('Unexpected token < in JSON at position 0')
      },
    }

    await expect(readJson(response)).rejects.toThrow(
      /did not send a valid reply \(status 404\).*API may be offline/,
    )
  })

  it('shows that message when sign-in reaches a server with no API', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => {
          throw new SyntaxError('Unexpected token < in JSON at position 0')
        },
      }),
    )

    await expect(login('a@example.com', 'a-long-password')).rejects.toThrow(
      /API may be offline/,
    )

    vi.unstubAllGlobals()
  })
})
