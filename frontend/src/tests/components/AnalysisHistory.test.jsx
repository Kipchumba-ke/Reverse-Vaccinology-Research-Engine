import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import AnalysisHistory from '../../components/AnalysisHistory'
import { getAnalysisHistory } from '../../services/historyService'

vi.mock('../../services/historyService', () => ({
  getAnalysisHistory: vi.fn(),
}))

beforeEach(() => {
  localStorage.setItem('token', 'test-token')
  vi.clearAllMocks()
})

afterEach(() => {
  cleanup()
  localStorage.clear()
})

function renderHistory() {
  return render(
    <MemoryRouter>
      <AnalysisHistory />
    </MemoryRouter>,
  )
}

describe('AnalysisHistory', () => {
  it('displays a loading state while history is being fetched', () => {
    getAnalysisHistory.mockReturnValue(new Promise(() => {}))

    renderHistory()

    expect(screen.getByText(/loading analysis history/i)).toBeInTheDocument()
  })

  it('renders the current user’s analysis records', async () => {
    getAnalysisHistory.mockResolvedValue([
      {
        analysis_id: 'analysis-123',
        protein_name: 'Example protein',
        organism: 'Example organism',
        accession: 'ABC123',
        created_at: '2026-10-20T10:30:00',
        status: 'completed',
      },
    ])

    renderHistory()

    expect(await screen.findByRole('heading', { name: 'Analysis History' }))
      .toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Example protein' }))
      .toBeInTheDocument()
    expect(screen.getByText('Example organism')).toBeInTheDocument()
    expect(screen.getByText('Accession: ABC123')).toBeInTheDocument()
    expect(screen.getByText(/Status:/i)).toHaveTextContent('completed')

    const link = screen.getByRole('link', { name: /view analysis/i })
    expect(link).toHaveAttribute('href', '/analyses/analysis-123')

    expect(getAnalysisHistory).toHaveBeenCalledWith('test-token')
  })

  it('shows an empty state when there are no analyses', async () => {
    getAnalysisHistory.mockResolvedValue([])

    renderHistory()

    expect(
      await screen.findByText(/you have no saved analyses yet/i),
    ).toBeInTheDocument()
  })

  it('displays an error when history cannot be loaded', async () => {
    getAnalysisHistory.mockRejectedValue(new Error('Unable to load history.'))

    renderHistory()

    expect(await screen.findByRole('alert'))
      .toHaveTextContent('Unable to load history.')
    await waitFor(() => {
      expect(screen.queryByText(/loading analysis history/i)).not.toBeInTheDocument()
    })
  })

  it('handles missing optional metadata', async () => {
    getAnalysisHistory.mockResolvedValue([
      {
        analysis_id: 'analysis-456',
        status: 'pending',
      },
    ])

    renderHistory()

    expect(await screen.findByRole('heading', { name: 'Unnamed protein' }))
      .toBeInTheDocument()
    expect(screen.getByText('Organism not specified')).toBeInTheDocument()
    expect(screen.getByText('Created: Date unavailable')).toBeInTheDocument()
  })
})
