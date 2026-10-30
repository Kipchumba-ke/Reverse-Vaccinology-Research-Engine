import { describe, it, expect } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import SequenceTracks from '../../components/SequenceTracks'
import { makeReport } from '../fixtures/sequenceReport'

describe('SequenceTracks', () => {
  it('renders an accessible feature map', () => {
    render(<SequenceTracks report={makeReport()} />)

    expect(
      screen.getByRole('img', { name: 'Sequence feature map' }),
    ).toBeInTheDocument()
  })

  it('labels each track', () => {
    render(<SequenceTracks report={makeReport()} />)

    const chart = screen.getByRole('img', { name: 'Sequence feature map' })

    expect(within(chart).getByText('Signal peptide (ReverseVax rules)')).toBeInTheDocument()
    expect(within(chart).getByText('B-cell epitopes (IEDB Bepipred-2.0)')).toBeInTheDocument()
    expect(within(chart).getByText('MHC class I binders (IEDB)')).toBeInTheDocument()
  })

  it('gives every region a hover title', () => {
    render(<SequenceTracks report={makeReport()} />)

    const chart = screen.getByRole('img', { name: 'Sequence feature map' })
    const titles = [...chart.querySelectorAll('rect title')].map((t) => t.textContent)

    expect(titles.some((t) => /Signal peptide, cleavage after 22/.test(t))).toBe(true)
    expect(titles.some((t) => /binds 2 allele/.test(t))).toBe(true)
  })

  it('offers the same information as text', () => {
    render(<SequenceTracks report={makeReport()} />)

    expect(screen.getByText('Show the same features as text')).toBeInTheDocument()
    expect(screen.getByText(/: 1-22/)).toBeInTheDocument()
  })

  it('says so when there is nothing to draw', () => {
    render(<SequenceTracks report={{ protein: { length: 50 }, measurements: {} }} />)

    expect(screen.getByText(/No signal peptide, topology or epitope features/)).toBeInTheDocument()
    expect(screen.queryByRole('img')).not.toBeInTheDocument()
  })
})
