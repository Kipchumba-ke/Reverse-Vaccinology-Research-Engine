import { describe, expect, it, vi, beforeEach } from 'vitest'
import { register } from '../../services/authService'

describe('register', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('sends email and password to the register endpoint', async () => {
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValue({
        ok: true,
        json: async () => ({
          user_id: '123',
        }),
      })

    await register('test@example.com', 'password123')

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/register',
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'password123',
        }),
      },
    )
  })
})
