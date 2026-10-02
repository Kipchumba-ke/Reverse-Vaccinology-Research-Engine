import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { submitAnalysis } from '../../services/analysisService'
import App from '../../App'

vi.mock('../../services/analysisService', () => ({
  submitAnalysis: vi.fn().mockResolvedValue({
    analysis_id: '123',
    status: 'pending',
  }),
}))

describe('App', () => {
  it('renders the reverse vaccinology application', () => {
    render(<App />)

    expect(
      screen.getByRole('heading', {
        name: /reverse vaccinology/i,
      }),
    ).toBeInTheDocument()
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

  it('submits the protein sequence through the analysis service', async () => {
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

    expect(submitAnalysis).toHaveBeenCalledWith(
      'MKTIIALSYIFCLVFADYKDDDDK',
    )
  })

  it('shows an error when protein analysis submission fails', async () => {
    const user = userEvent.setup()

    submitAnalysis.mockRejectedValueOnce(
      new Error('Analysis submission failed'),
    )

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
      screen.getByText(/analysis submission failed/i),
    ).toBeInTheDocument()

    expect(
      screen.queryByText(/analysis submitted/i),
    ).not.toBeInTheDocument()
  })
})