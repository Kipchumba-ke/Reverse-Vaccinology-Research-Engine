import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Register from '../../components/Register'

vi.mock('../../services/authService', () => ({
  register: vi.fn(),
}))

import { register } from '../../services/authService'

describe('Register', () => {
  it('allows a user to submit their email and password', async () => {
    const user = userEvent.setup()

    render(<Register />)

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
        name: /register/i,
      }),
    )

    expect(register).toHaveBeenCalledWith(
      'test@example.com',
      'password123',
    )
  })

  it('shows that registration was successful', async () => {
    const user = userEvent.setup()

    register.mockResolvedValue({
        user_id: '123',
    })

    render(<Register onRegister={() => {}} onLogin={() => {}} />)

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
        name: /register/i,
        }),
    )

    expect(
        await screen.findByText(/registration successful/i),
    ).toBeInTheDocument()
  })

  it('shows an error when registration fails', async () => {
    const user = userEvent.setup()

    register.mockRejectedValue(
        new Error('Email is already registered.'),
    )

    render(<Register />)

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
        name: /register/i,
        }),
    )

    expect(
        await screen.findByText(/email is already registered/i),
    ).toBeInTheDocument()
    })

    it('notifies the parent after successful registration', async () => {
        const onRegister = vi.fn()

        register.mockResolvedValue({
            user_id: '123',
        })

        const user = userEvent.setup()

        render(<Register onRegister={onRegister} />)

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
            name: /register/i,
            }),
        )

        expect(onRegister).toHaveBeenCalled()
    })

    it('allows a user to switch to login', async () => {
    const onLogin = vi.fn()
    const user = userEvent.setup()

    render(<Register onLogin={onLogin} />)

    await user.click(
        screen.getByRole('button', {
        name: /login/i,
        }),
    )

    expect(onLogin).toHaveBeenCalled()
    })
})