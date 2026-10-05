import { act ,render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { submitAnalysis, getAnalysisStatus } from '../../services/analysisService'
import App from '../../App'

vi.mock('../../services/analysisService', () => ({
  submitAnalysis: vi.fn().mockResolvedValue({
    analysis_id: '123',
    status: 'pending',
  }),
  getAnalysisStatus: vi.fn().mockResolvedValue({
    analysis_id: '123',
    status: 'running',
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

  it('displays the analysis id returned by the analysis service', async () => {
    const user = userEvent.setup()

    submitAnalysis.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'pending',
    })

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
      screen.getByText(/analysis id: 123/i),
    ).toBeInTheDocument()
  })

  it('displays the analysis status', async () => {
  const user = userEvent.setup()

  submitAnalysis.mockResolvedValueOnce({
    analysis_id: '123',
    status: 'pending',
  })

  getAnalysisStatus.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'pending',
    })

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
      screen.getByText(/status: pending/i),
    ).toBeInTheDocument()
  })

  it('displays a running analysis status', async () => {
    const user = userEvent.setup()

    submitAnalysis.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'pending',
    })

    getAnalysisStatus.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'running',
    })

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
      screen.getByText(/status: running/i),
    ).toBeInTheDocument()
  })

  it('checks the analysis status again while the analysis is running', async () => {
    vi.useFakeTimers()

    try {
      submitAnalysis.mockResolvedValueOnce({
        analysis_id: '123',
        status: 'pending',
      })

      getAnalysisStatus.mockResolvedValue({
        analysis_id: '123',
        status: 'running',
      })

      render(<App />)

      const input = screen.getByLabelText(/protein sequence/i)

      fireEvent.change(input, {
        target: {
          value: 'MKTIIALSYIFCLVFADYKDDDDK',
        },
      })

      await act(async () => {
        fireEvent.click(
          screen.getByRole('button', {
            name: /analyze protein/i,
          }),
        )

        await Promise.resolve()
      })

      expect(getAnalysisStatus).toHaveBeenCalledTimes(1)

      await act(async () => {
        await vi.advanceTimersByTimeAsync(1000)
      })

      expect(getAnalysisStatus).toHaveBeenCalledTimes(2)
    } finally {
      vi.useRealTimers()
    }
  })

  it('stops polling when the application is unmounted', async () => {
    vi.useFakeTimers()

    try {
      submitAnalysis.mockResolvedValueOnce({
        analysis_id: '123',
        status: 'pending',
      })

      getAnalysisStatus.mockResolvedValue({
        analysis_id: '123',
        status: 'running',
      })

      const { unmount } = render(<App />)

      const input = screen.getByLabelText(/protein sequence/i)

      fireEvent.change(input, {
        target: {
          value: 'MKTIIALSYIFCLVFADYKDDDDK',
        },
      })

      await act(async () => {
        fireEvent.click(
          screen.getByRole('button', {
            name: /analyze protein/i,
          }),
        )

        await Promise.resolve()
      })

      expect(getAnalysisStatus).toHaveBeenCalledTimes(1)

      unmount()

      await act(async () => {
        await vi.advanceTimersByTimeAsync(3000)
      })

      expect(getAnalysisStatus).toHaveBeenCalledTimes(1)
    } finally {
      vi.useRealTimers()
    }
  })

    it('displays the analysis report when the analysis is completed', async () => {
    vi.useFakeTimers()

    try {
      submitAnalysis.mockResolvedValueOnce({
        analysis_id: '123',
        status: 'pending',
      })

      getAnalysisStatus.mockResolvedValueOnce({
        analysis_id: '123',
        status: 'completed',
        report: {
          sequence: 'MKT',
          length: 3,
        },
      })

      render(<App />)

      const input = screen.getByLabelText(/protein sequence/i)

      fireEvent.change(input, {
        target: {
          value: 'MKT',
        },
      })

      await act(async () => {
        fireEvent.click(
          screen.getByRole('button', {
            name: /analyze protein/i,
          }),
        )

        await Promise.resolve()
      })

      expect(
        screen.getByText(/status: completed/i),
      ).toBeInTheDocument()

      expect(
        screen.getByText('MKT'),
      ).toBeInTheDocument()

      expect(
        screen.getByText(/length: 3/i),
      ).toBeInTheDocument()
    } finally {
      vi.useRealTimers()
    }
  })

    it('displays an error when the analysis fails', async () => {
    submitAnalysis.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'pending',
    })

    getAnalysisStatus.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'failed',
      report: null,
    })

    render(<App />)

    const input = screen.getByLabelText(/protein sequence/i)

    fireEvent.change(input, {
      target: {
        value: 'MKT',
      },
    })

    await act(async () => {
      fireEvent.click(
        screen.getByRole('button', {
          name: /analyze protein/i,
        }),
      )

      await Promise.resolve()
    })

    expect(
      screen.getByText(/analysis failed/i),
    ).toBeInTheDocument()
  })
})