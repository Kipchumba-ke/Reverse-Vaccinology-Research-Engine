import { act ,render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach ,describe, expect, it, vi } from 'vitest'
import { submitAnalysis, getAnalysisStatus } from '../../services/analysisService'
import { login } from '../../services/authService'
import App from '../../App'

vi.mock('../../services/analysisService', () => ({
  submitAnalysis: vi.fn(),
  getAnalysisStatus: vi.fn(),
}))

vi.mock('../../services/authService', () => ({
  login: vi.fn(),
}))

describe('App', () => {

  beforeEach(() => {
    localStorage.setItem('token', 'test_token')
    submitAnalysis.mockReset()
    getAnalysisStatus.mockReset()

    login.mockReset()
    login.mockResolvedValue({
      user_id: '1',
      token: 'test_token',
    })

    submitAnalysis.mockResolvedValue({
      analysis_id: '123',
      status: 'pending',
    })

    getAnalysisStatus.mockResolvedValue({
      analysis_id: '123',
      status: 'running',
    })

  })

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
    localStorage.setItem('token', 'test_token')

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
      'test_token'
    )
  })

  it('passes the stored authentication token when submitting an analysis', async () => {
    const user = userEvent.setup()

    localStorage.setItem('token', 'test_token')

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
      'test_token',
    )
  })

  it('passes the stored authentication token when polling analysis status', async () => {
    const user = userEvent.setup()

    localStorage.setItem('token', 'test_token')

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

    await waitFor(() => {
      expect(getAnalysisStatus).toHaveBeenCalledWith(
        '123',
        'test_token',
      )
    })
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
          protein: {
            sequence: 'MKT',
            length: 3,
          },
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

  it('displays report metadata from the analysis report', async () => {
    getAnalysisStatus.mockResolvedValue({
      analysis_id: '123',
      status: 'completed',
      report: {
        metadata: {
          report_type: 'reverse_vaccinology',
          report_version: '1.0',
          analysis_pipeline: 'protein_sequence_analysis',
        },
      },
    })

    render(<App />)

    fireEvent.change(
      screen.getByRole('textbox'),
      { target: { value: 'MKTLLILAV' } },
    )

    fireEvent.click(
      screen.getByRole('button', { name: /analyze/i }),
    )

    expect(
      await screen.findByText(
        /report type: reverse_vaccinology/i,
      ),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/report version: 1.0/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(
        /analysis pipeline: protein_sequence_analysis/i,
      ),
    ).toBeInTheDocument()
  })

  it('displays the protein characteristics from the analysis report', async () => {
    submitAnalysis.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'pending',
    })

    getAnalysisStatus.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'completed',
      report: {
        protein: {
          id: 'P12345',
          name: 'Example Protein',
          organism: 'Example bacterium',
          accession: 'ABC123',
          sequence: 'MKT',
          length: 3,
          molecular_weight: 345.67,
          gravy: 0.42,
          isoelectric_point: 6.8,
        },
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
      screen.getByText(/molecular weight: 345.67/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/gravy: 0.42/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/isoelectric point: 6.8/i),
    ).toBeInTheDocument()

    expect(
    screen.getByText(/protein id: P12345/i),
  ).toBeInTheDocument()

  expect(
    screen.getByText(/name: example protein/i),
  ).toBeInTheDocument()

  expect(
    screen.getByText(/organism: example bacterium/i),
  ).toBeInTheDocument()

  expect(
    screen.getByText(/accession: ABC123/i),
  ).toBeInTheDocument()
  })

  it('displays hydrophobicity measurements from the analysis report', async () => {
    submitAnalysis.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'pending',
    })

    getAnalysisStatus.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'completed',
      report: {
        measurements: {
          composition: {
            length: 346,
            counts: {
              A: 10,
              C: 2,
              G: 8,
            },
            percentages: {
              A: 2.89,
              C: 0.58,
              G: 2.31,
            },
          },
          charge_and_hydrophobicity: {
            net_charge: -1.2,
          },
          hydropathy_profile: [
            {
              position: 1,
              value: 0.5,
            },
            {
              position: 2,
              value: 1.2,
            },
          ],
          hydrophobic_regions: [
            {
              start: 5,
              end: 12,
              length: 8,
            },
          ],
        },
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
      screen.getByText(/net charge: -1.2/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/hydrophobic region: 5-12/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/composition length: 346/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/composition count: A 10/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/composition count: C 2/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/composition count: G 8/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/composition percentage: A 2.89%/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/composition percentage: C 0.58%/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/composition percentage: G 2.31%/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/hydropathy: position 1, value 0.5/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/hydropathy: position 2, value 1.2/i),
    ).toBeInTheDocument()
  })

  it('displays transmembrane candidates from the analysis report', async () => {
    submitAnalysis.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'pending',
    })

    getAnalysisStatus.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'completed',
      report: {
        measurements: {
          transmembrane_candidates: [
            {
              start: 20,
              end: 42,
              length: 23,
            },
          ],
        },
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
      screen.getByText(/transmembrane candidate: 20-42/i),
    ).toBeInTheDocument()
  })

  it('displays conservation results from the analysis report', async () => {
    submitAnalysis.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'pending',
    })

    getAnalysisStatus.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'completed',
      report: {
        conservation: {
          summary: {
            conservation_percentage: 85.0,
            alignment_length: 120,
            sequence_count: 5,
          },
          regions: [
            {
              start: 10,
              end: 25,
              length: 16,
            },
          ],
        },
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
      screen.getByText(/conservation: 85%/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/alignment length: 120/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/sequences analyzed: 5/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/conserved region: 10-25/i),
    ).toBeInTheDocument()
  })

  it('displays localization evidence from the analysis report', async () => {
    submitAnalysis.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'pending',
    })

    getAnalysisStatus.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'completed',
      report: {
        evidence: {
          localization: [
            {
              source: 'UniProt',
              location: 'cell membrane',
              confidence: 'high',
            },
          ],
        },
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
      screen.getByText(/localization: cell membrane/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/source: UniProt/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/confidence: high/i),
    ).toBeInTheDocument()
  })

  it('displays essentiality evidence from the analysis report', async () => {
    submitAnalysis.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'pending',
    })

    getAnalysisStatus.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'completed',
      report: {
        evidence: {
          essentiality: [
            {
              source: 'Database',
              evidence: 'Essential gene',
              confidence: 'high',
            },
          ],
        },
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
      screen.getByText(/essentiality: essential gene/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/source: Database/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/confidence: high/i),
    ).toBeInTheDocument()
  })

  it('displays host similarity evidence from the analysis report', async () => {
    submitAnalysis.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'pending',
    })

    getAnalysisStatus.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'completed',
      report: {
        evidence: {
          host_similarity: [
            {
              source: 'BLAST',
              identity_percentage: 12.5,
              alignment_length: 180,
              e_value: 0.01,
              confidence: 'low',
            },
          ],
        },
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
      screen.getByText(/host similarity: 12.5%/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/alignment length: 180/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/e-value: 0.01/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/source: BLAST/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/confidence: low/i),
    ).toBeInTheDocument()
  })

  it('displays interpretations from the analysis report', async () => {
    submitAnalysis.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'pending',
    })

    getAnalysisStatus.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'completed',
      report: {
        interpretations: [
          {
            category: 'hydrophobicity',
            interpretation: 'The protein contains moderately hydrophobic regions.',
            confidence: 'medium',
          },
        ],
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
      screen.getByText(
        /the protein contains moderately hydrophobic regions/i,
      ),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/category: hydrophobicity/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/confidence: medium/i),
    ).toBeInTheDocument()
  })

  it('displays the candidate assessment from the analysis report', async () => {
    submitAnalysis.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'pending',
    })

    getAnalysisStatus.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'completed',
      report: {
        candidate_assessment: {
          category: 'promising',
          score: 0.82,
          rationale: 'Multiple computational evidence types support further investigation.',
        },
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
      screen.getByText(/category: promising/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/score: 0.82/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(
        /multiple computational evidence types support further investigation/i,
      ),
    ).toBeInTheDocument()
  })

  it('displays limitations from the analysis report', async () => {
    submitAnalysis.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'pending',
    })

    getAnalysisStatus.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'completed',
      report: {
        limitations: [
          'Computational evidence does not replace experimental validation.',
          'Results depend on the quality of the available reference data.',
        ],
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
      screen.getByText(
        /computational evidence does not replace experimental validation/i,
      ),
    ).toBeInTheDocument()

    expect(
      screen.getByText(
        /results depend on the quality of the available reference data/i,
      ),
    ).toBeInTheDocument()
  })

  it('displays peptide candidates from the analysis report', async () => {
    submitAnalysis.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'pending',
    })

    getAnalysisStatus.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'completed',
      report: {
        peptide_candidates: [
          {
            sequence: 'MKTLLV',
            start: 10,
            end: 15,
            length: 6,
          },
        ],
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
      screen.getByText(/peptide candidate: MKTLLV/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/position: 10-15/i),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/length: 6/i),
    ).toBeInTheDocument()
  })

  it('displays scientific sections in the analysis report', async () => {
    getAnalysisStatus.mockResolvedValue({
      analysis_id: '123',
      status: 'completed',
      report: {
        metadata: {
          report_type: 'reverse_vaccinology',
          report_version: '1.0',
          analysis_pipeline: 'protein_sequence_analysis',
        },
        protein: {
          id: 'protein-1',
          name: 'Test Protein',
          organism: 'Test Organism',
          accession: 'ABC123',
          sequence: 'MKTLLILAV',
          length: 9,
          molecular_weight: 1000,
          gravy: 0.5,
          isoelectric_point: 7.0,
        },
        measurements: {
          charge_and_hydrophobicity: {
            net_charge: 1,
          },
        },
        conservation: {},
        evidence: {},
        interpretations: [],
        candidate_assessment: {},
        limitations: [],
        peptide_candidates: [],
      },
    })

    render(<App />)

    fireEvent.change(
      screen.getByRole('textbox'),
      { target: { value: 'MKTLLILAV' } },
    )

    fireEvent.click(
      screen.getByRole('button', { name: /analyze/i }),
    )

    expect(
      await screen.findByRole('heading', {
        name: /report metadata/i,
      }),
    ).toBeInTheDocument()

    expect(
      screen.getByRole('heading', {
        name: /protein characteristics/i,
      }),
    ).toBeInTheDocument()

    expect(
      screen.getByRole('heading', {
        name: /measurements/i,
      }),
    ).toBeInTheDocument()

    expect(
      screen.getByRole('heading', {
        name: /conservation/i,
      }),
    ).toBeInTheDocument()

    expect(
      screen.getByRole('heading', {
        name: /evidence/i,
      }),
    ).toBeInTheDocument()

    expect(
      screen.getByRole('heading', {
        name: /interpretations/i,
      }),
    ).toBeInTheDocument()

    expect(
      screen.getByRole('heading', {
        name: /candidate assessment/i,
      }),
    ).toBeInTheDocument()

    expect(
      screen.getByRole('heading', {
        name: /limitations/i,
      }),
    ).toBeInTheDocument()

    expect(
      screen.getByRole('heading', {
        name: /peptide candidates/i,
      }),
    ).toBeInTheDocument()
  })

  it('groups scientific report content into sections', async () => {
    getAnalysisStatus.mockResolvedValue({
      analysis_id: '123',
      status: 'completed',
      report: {
        metadata: {
          report_type: 'reverse_vaccinology',
          report_version: '1.0',
          analysis_pipeline: 'protein_sequence_analysis',
        },
        protein: {
          id: 'protein-1',
          name: 'Test Protein',
          organism: 'Test Organism',
          accession: 'ABC123',
          sequence: 'MKTLLILAV',
          length: 9,
          molecular_weight: 1000,
          gravy: 0.5,
          isoelectric_point: 7.0,
        },
        measurements: {
          charge_and_hydrophobicity: {
            net_charge: 1,
          },
        },
        conservation: {},
        evidence: {},
        interpretations: [],
        candidate_assessment: {},
        limitations: [],
        peptide_candidates: [],
      },
    })

    render(<App />)

    fireEvent.change(
      screen.getByRole('textbox'),
      { target: { value: 'MKTLLILAV' } },
    )

    fireEvent.click(
      screen.getByRole('button', { name: /analyze/i }),
    )

    expect(
      await screen.findByRole('heading', {
        name: /report metadata/i,
      }),
    ).toBeInTheDocument()

    expect(
      screen.getByRole('heading', {
        name: /report metadata/i,
      }).closest('section'),
    ).toBeInTheDocument()

    expect(
      screen.getByRole('heading', {
        name: /protein characteristics/i,
      }).closest('section'),
    ).toBeInTheDocument()

    expect(
      screen.getByRole('heading', {
        name: /measurements/i,
      }).closest('section'),
    ).toBeInTheDocument()

    expect(
      screen.getByRole('heading', {
        name: /conservation/i,
      }).closest('section'),
    ).toBeInTheDocument()

    expect(
      screen.getByRole('heading', {
        name: /evidence/i,
      }).closest('section'),
    ).toBeInTheDocument()

    expect(
      screen.getByRole('heading', {
        name: /interpretations/i,
      }).closest('section'),
    ).toBeInTheDocument()

    expect(
      screen.getByRole('heading', {
        name: /candidate assessment/i,
      }).closest('section'),
    ).toBeInTheDocument()

    expect(
      screen.getByRole('heading', {
        name: /limitations/i,
      }).closest('section'),
    ).toBeInTheDocument()

    expect(
      screen.getByRole('heading', {
        name: /peptide candidates/i,
      }).closest('section'),
    ).toBeInTheDocument()
  })

  it('provides stable styling hooks for the analysis report', async () => {
    getAnalysisStatus.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'completed',
      report: {
        metadata: {
          report_type: 'reverse_vaccinology',
          report_version: '1.0',
          analysis_pipeline: 'protein_sequence_analysis',
        },
        protein: {
          id: 'protein-1',
          name: 'Test Protein',
          organism: 'Test Organism',
          accession: 'ABC123',
          sequence: 'MKTLLILAV',
          length: 9,
          molecular_weight: 1000,
          gravy: 0.5,
          isoelectric_point: 7.0,
        },
        measurements: {
          charge_and_hydrophobicity: {
            net_charge: 1,
          },
        },
        conservation: {},
        evidence: {},
        interpretations: [],
        candidate_assessment: {},
        limitations: [],
        peptide_candidates: [],
      },
    })

    render(<App />)

    fireEvent.change(
      screen.getByRole('textbox'),
      { target: { value: 'MKTLLILAV' } },
    )

    fireEvent.click(
      screen.getByRole('button', { name: /analyze/i }),
    )

    const report = await screen.findByRole('heading', {
      name: /analysis report/i,
    })

    expect(
      report.closest('.analysis-report'),
    ).toBeInTheDocument()

    expect(
      document.querySelectorAll('.analysis-report-section'),
    ).toHaveLength(9)
  })

  it('marks each scientific section for visual separation', async () => {
    getAnalysisStatus.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'completed',
      report: {
        metadata: {
          report_type: 'reverse_vaccinology',
          report_version: '1.0',
          analysis_pipeline: 'protein_sequence_analysis',
        },
        protein: {
          id: 'protein-1',
          name: 'Test Protein',
          organism: 'Test Organism',
          accession: 'ABC123',
          sequence: 'MKTLLILAV',
          length: 9,
          molecular_weight: 1000,
          gravy: 0.5,
          isoelectric_point: 7.0,
        },
        measurements: {
          charge_and_hydrophobicity: {
            net_charge: 1,
          },
        },
        conservation: {},
        evidence: {},
        interpretations: [],
        candidate_assessment: {},
        limitations: [],
        peptide_candidates: [],
      },
    })

    render(<App />)

    fireEvent.change(
      screen.getByRole('textbox'),
      { target: { value: 'MKTLLILAV' } },
    )

    fireEvent.click(
      screen.getByRole('button', { name: /analyze/i }),
    )

    await screen.findByRole('heading', {
      name: /analysis report/i,
    })

    const sections = document.querySelectorAll(
      '.analysis-report-section',
    )

    expect(sections).toHaveLength(9)

    sections.forEach((section) => {
      expect(section).toHaveClass(
        'analysis-report-section',
      )
    })
  })

  it('provides styling hooks for the analysis interface', () => {
    render(<App />)

    expect(
      screen.getByRole('heading', {
        name: /reverse vaccinology/i,
      }).closest('.analysis-page'),
    ).toBeInTheDocument()

    expect(
      screen.getByLabelText(/protein sequence/i).closest(
        '.analysis-form',
      ),
    ).toBeInTheDocument()

    expect(
      screen.getByRole('button', {
        name: /analyze protein/i,
      }),
    ).toHaveClass('analysis-submit')
  })

  it('provides stable styling hooks for the report overview', async () => {
    const report = {
      metadata: {
        report_type: 'reverse_vaccinology',
        report_version: '1.0',
        analysis_pipeline: 'protein_sequence_analysis',
      },
      protein: {
        id: 'P001',
        name: 'Example Protein',
        organism: 'Example Organism',
        accession: 'ABC123',
        sequence: 'MKTIIALSYIFCLVFADYKDDDDK',
        length: 25,
        molecular_weight: 2800,
        gravy: -0.2,
        isoelectric_point: 6.5,
      },
    }

    getAnalysisStatus.mockResolvedValue({
      analysis_id: '123',
      status: 'completed',
      report,
    })

    render(<App />)

    await act(async () => {
      fireEvent.click(
        screen.getByRole('button', {
          name: /analyze protein/i,
        }),
      )
    })

    expect(
      screen.getByText(/report metadata/i).closest(
        '.report-overview',
      ),
    ).toBeInTheDocument()

    expect(
      screen.getByText(/protein characteristics/i),
    ).toBeInTheDocument()
  })

  it('shows the login screen when the user is not authenticated', () => {
    localStorage.removeItem('token')

    render(<App />)

    expect(
      screen.getByRole('button', {
        name: /login/i,
      }),
    ).toBeInTheDocument()

    expect(
      screen.getByLabelText(/email/i),
    ).toBeInTheDocument()

    expect(
      screen.queryByLabelText(/protein sequence/i),
    ).not.toBeInTheDocument()
  })

  it('shows the analysis application after a successful login', async () => {
    localStorage.removeItem('token')

    const user = userEvent.setup()

    render(<App />)

    await user.type(
      screen.getByLabelText(/email/i),
      'test@example.com',
    )

    await user.type(
      screen.getByLabelText(/password/i),
      'password123',
    )

    await user.click(
      screen.getByRole('button', { name: /login/i }),
    )

    expect(
      screen.getByLabelText(/protein sequence/i),
    ).toBeInTheDocument()
  })

  it('allows an unauthenticated user to switch to registration', async () => {
    localStorage.removeItem('token')

    const user = userEvent.setup()

    render(<App />)

    await user.click(
      screen.getByRole('button', {
        name: /register/i,
      }),
    )

    expect(
      screen.getByLabelText(/email/i),
    ).toBeInTheDocument()

    expect(
      screen.getByRole('button', {
        name: /^register$/i,
      }),
    ).toBeInTheDocument()
  })

  it('allows an unauthenticated user to switch from registration to login', async () => {
    localStorage.removeItem('token')

    const user = userEvent.setup()

    render(<App />)

    await user.click(
      screen.getByRole('button', {
        name: /register/i,
      }),
    )

    await user.click(
      screen.getByRole('button', {
        name: /already have an account\? login/i,
      }),
    )

    expect(
      screen.getByLabelText(/email/i),
    ).toHaveAttribute('id', 'login-email')

    expect(
      screen.getByRole('button', {
        name: /^login$/i,
      }),
    ).toBeInTheDocument()
  })

  it('groups protein characteristics into a structured grid', async () => {
    getAnalysisStatus.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'completed',
      report: {
        protein: {
          id: 'protein-1',
          name: 'Test Protein',
          organism: 'Test Organism',
          accession: 'ABC123',
          sequence: 'MKTLLILAV',
          length: 9,
          molecular_weight: 1000,
          gravy: 0.5,
          isoelectric_point: 7.0,
        },
      },
    })

    render(<App />)

    fireEvent.change(
      screen.getByLabelText(/protein sequence/i),
      {
        target: {
          value: 'MKTLLILAV',
        },
      },
    )

    fireEvent.click(
      screen.getByRole('button', {
        name: /analyze protein/i,
      }),
    )

    await screen.findByRole('heading', {
      name: /protein characteristics/i,
    })

    expect(
      screen.getByText(/protein id/i).closest(
        '.protein-characteristics-grid',
      ),
    ).toBeInTheDocument()
  })

  it('renders the protein sequence in a dedicated sequence block', async () => {
    getAnalysisStatus.mockResolvedValueOnce({
      analysis_id: '123',
      status: 'completed',
      report: {
        protein: {
          sequence: 'MKTLLILAV',
        },
      },
    })

    render(<App />)

    fireEvent.change(
      screen.getByLabelText(/protein sequence/i),
      {
        target: {
          value: 'MKTLLILAV',
        },
      },
    )

    fireEvent.click(
      screen.getByRole('button', {
        name: /analyze protein/i,
      }),
    )

    await screen.findByRole('heading', {
      name: /protein characteristics/i,
    })

    const sequence = screen.getByText('MKTLLILAV', {
      selector: '.protein-sequence p',
    })

    expect(
      sequence.closest('.protein-sequence'),
    ).toBeInTheDocument()
  })
})