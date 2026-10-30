import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import StructureViewer from '../../components/StructureViewer'
import { SAMPLE_PDB } from '../fixtures/sequenceReport'

function model(overrides = {}) {
  return {
    accession: 'P0A911',
    entry_id: 'AF-P0A911-F1',
    model_version: 4,
    mean_plddt: 69.6,
    source: 'AlphaFold Protein Structure Database',
    reference_sequence: 'MKT',
    pdb: SAMPLE_PDB,
    ...overrides,
  }
}

function respondWith(body, ok = true) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok,
      status: ok ? 200 : 404,
      json: async () => body,
    }),
  )
}

describe('StructureViewer', () => {
  beforeEach(() => {
    localStorage.setItem('token', 'test-token')
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  it('explains why there is no structure without a UniProt accession', () => {
    render(<StructureViewer accession="ABC123" sequence="MKT" />)

    expect(screen.getByText(/UniProt accession/)).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('does not fetch until asked', () => {
    respondWith(model())

    render(<StructureViewer accession="P0A911" sequence="MKT" />)

    expect(fetch).not.toHaveBeenCalled()
    expect(
      screen.getByRole('button', { name: 'Load predicted 3-D structure' }),
    ).toBeInTheDocument()
  })

  it('loads the model with the stored token and shows the viewer', async () => {
    respondWith(model())
    const user = userEvent.setup()

    render(<StructureViewer accession="p0a911" sequence="MKT" />)
    await user.click(screen.getByRole('button', { name: 'Load predicted 3-D structure' }))

    expect(
      await screen.findByRole('img', { name: /Predicted 3-D backbone of P0A911/ }),
    ).toBeInTheDocument()
    expect(fetch).toHaveBeenCalledWith(
      '/api/structure/P0A911',
      expect.objectContaining({
        headers: { Authorization: 'Bearer test-token' },
      }),
    )
    expect(screen.getByText(/mean pLDDT 69.6/)).toBeInTheDocument()
  })

  it('warns when the model is for a different sequence', async () => {
    respondWith(model({ reference_sequence: 'MKTX' }))
    const user = userEvent.setup()

    render(<StructureViewer accession="P0A911" sequence="MKT" />)
    await user.click(screen.getByRole('button', { name: 'Load predicted 3-D structure' }))

    expect(await screen.findByText(/differs from the sequence analysed/)).toBeInTheDocument()
  })

  it('does not warn when the sequences match', async () => {
    respondWith(model())
    const user = userEvent.setup()

    render(<StructureViewer accession="P0A911" sequence="MKT" />)
    await user.click(screen.getByRole('button', { name: 'Load predicted 3-D structure' }))
    await screen.findByRole('img', { name: /Predicted 3-D backbone/ })

    expect(screen.queryByText(/differs from the sequence analysed/)).not.toBeInTheDocument()
  })

  it('shows the confidence legend and switches colour modes', async () => {
    respondWith(model())
    const user = userEvent.setup()

    render(
      <StructureViewer
        accession="P0A911"
        sequence="MKT"
        tracks={[{ id: 'signal', label: 'Signal peptide', color: '#0072B2', segments: [] }]}
      />,
    )
    await user.click(screen.getByRole('button', { name: 'Load predicted 3-D structure' }))
    await screen.findByRole('img', { name: /Predicted 3-D backbone/ })

    expect(screen.getByText('Very high (> 90)')).toBeInTheDocument()

    await user.selectOptions(screen.getByLabelText(/Colour by/), 'annotation')

    expect(screen.getByText('Signal peptide')).toBeInTheDocument()
    expect(screen.queryByText('Very high (> 90)')).not.toBeInTheDocument()
  })

  it('shows the server error when no model exists', async () => {
    respondWith({ error: 'AlphaFold DB has no model for P0A911.' }, false)
    const user = userEvent.setup()

    render(<StructureViewer accession="P0A911" sequence="MKT" />)
    await user.click(screen.getByRole('button', { name: 'Load predicted 3-D structure' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('no model for P0A911')
  })
})
