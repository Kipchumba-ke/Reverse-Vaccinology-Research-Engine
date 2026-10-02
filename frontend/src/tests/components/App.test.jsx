import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
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