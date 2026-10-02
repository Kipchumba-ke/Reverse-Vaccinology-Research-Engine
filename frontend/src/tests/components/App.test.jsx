import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import userEvent from '@testing-library/user-event'
import App from '../../App'

describe('App', () => {
  it('renders the reverse vaccinology application', () => {
    render(<App />)

    expect(
      screen.getByRole('heading', {
        name: /reverse vaccinology/i,
      }),
    ).toBeInTheDocument()
  })
})

it('renders a protein sequence input', () => {
  render(<App />)

  expect(
    screen.getByLabelText(/protein sequence/i),
  ).toBeInTheDocument()
})

it('renders a button to submit the protein sequence', () => {
  render(<App />)

  expect(
    screen.getByRole('button', {
      name: /analyze protein/i,
    }),
  ).toBeInTheDocument()
})

it('captures the submitted protein sequence', async () => {
  render(<App />)

  const input = screen.getByLabelText(/protein sequence/i)

  await userEvent.type(
    input,
    'MKTIIALSYIFCLVFADYKDDDDK',
  )

  await userEvent.click(
    screen.getByRole('button', {
      name: /analyze protein/i,
    }),
  )

  expect(input).toHaveValue(
    'MKTIIALSYIFCLVFADYKDDDDK',
  )
})

it('shows that the protein analysis has been submitted', async () => {
  const user = userEvent.setup()

  render(<App />)

  const input = screen.getByLabelText(/protein sequence/i)

  await user.type(
    input,
    'MKTIIALSYIFCLVFADYKDDDDK',
  )

  await user.click(
    screen.getByRole('button', {
      name: /analyze protein/i,
    }),
  )

  expect(
    screen.getByText(/analysis submitted/i),
  ).toBeInTheDocument()
})
