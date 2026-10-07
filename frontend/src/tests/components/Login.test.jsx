import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Login from '../../components/Login'

vi.mock('../../services/authService', () => ({
  login: vi.fn(),
}))

import { login } from '../../services/authService'

describe('Login', () => {
  it('allows a user to submit their email and password', async () => {
    const user = userEvent.setup()

    render(<Login />)

    await user.type(
      screen.getByLabelText(/email/i),
      'test@example.com',
    )

    await user.type(
      screen.getByLabelText(/password/i),
      'password123',
    )

    await user.click(
      screen.getByRole('button', {
        name: /login/i,
      }),
    )

    expect(login).toHaveBeenCalledWith(
      'test@example.com',
      'password123',
    )
  })

  it('shows that login was successful', async () => {
    const user = userEvent.setup()

    login.mockResolvedValue({
        user_id: '123',
        token: 'test_token',
    })

    render(<Login onLogin={() => {}} />)

    await user.type(
        screen.getByLabelText(/email/i),
        'test@example.com',
    )

    await user.type(
        screen.getByLabelText(/password/i),
        'password123',
    )

    await user.click(
        screen.getByRole('button', {
        name: /login/i,
        }),
    )

    expect(
        await screen.findByText(/login successful/i),
    ).toBeInTheDocument()
    })

    it('shows an error when login fails', async () => {
        const user = userEvent.setup()

        login.mockRejectedValue(
            new Error('Invalid email or password.'),
        )

        render(<Login />)

        await user.type(
            screen.getByLabelText(/email/i),
            'test@example.com',
        )

        await user.type(
            screen.getByLabelText(/password/i),
            'wrong-password',
        )

        await user.click(
            screen.getByRole('button', {
            name: /login/i,
            }),
        )

        expect(
            await screen.findByText(/invalid email or password/i),
        ).toBeInTheDocument()
    })
    
    it('notifies the parent after a successful login', async () => {
        const onLogin = vi.fn()

        login.mockResolvedValue({
            user_id: '1',
            token: 'test_token',
        })

        const user = userEvent.setup()

        render(<Login onLogin={onLogin} />)

        await user.type(screen.getByLabelText(/email/i), 'test@example.com')
        await user.type(screen.getByLabelText(/password/i), 'password123')
        await user.click(screen.getByRole('button', { name: /login/i }))

        expect(onLogin).toHaveBeenCalled()
    })
})