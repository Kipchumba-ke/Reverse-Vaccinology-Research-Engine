import { describe, expect, it, vi } from 'vitest'
import { login } from '../../services/authService'

describe('login', () => {
  it('sends email and password to the login API', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        user_id: '123',
        token: 'test_token',
      }),
    })

    globalThis.fetch = fetchMock

    const result = await login(
      'test@example.com',
      'password123',
    )

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/login',
      expect.objectContaining({
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: 'test@example.com',
          password: 'password123',
        }),
      }),
    )

    expect(result).toEqual({
      user_id: '123',
      token: 'test_token',
    })
  })

  it('stores the authentication token after a successful login', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
        user_id: '123',
        token: 'test_token',
        }),
    })

    globalThis.fetch = fetchMock

    await login(
        'test@example.com',
        'password123',
    )

    expect(localStorage.getItem('token')).toBe('test_token')
    })

    it('rejects when the login request is unauthorized', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
        json: async () => ({
        error: 'Invalid email or password.',
        }),
    })

    globalThis.fetch = fetchMock

    await expect(
        login('test@example.com', 'wrong-password'),
    ).rejects.toThrow('Invalid email or password.')
    })
})