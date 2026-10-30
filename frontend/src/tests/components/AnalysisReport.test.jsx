import { describe, it, expect } from 'vitest'
import { fireEvent, render, screen, within } from '@testing-library/react'
import AnalysisReport from '../../components/AnalysisReport'
import realReport from '../fixtures/realReport.json'

function reportWithHostHits(count) {
  const report = structuredClone(realReport)
  report.evidence.host_similarity = Array.from({ length: count }, (_, index) => ({
    host_id: `host_${index + 1}`,
    identity_percentage: 20 + index * 1.23456789,
    alignment_length: 80 + index,
    query_coverage_percentage: 41.666666666,
    subject_coverage_percentage: 33.333333333,
    e_value: 0.0000123,
    source: 'BLASTP',
    confidence: 'medium',
  }))
  return report
}

describe('AnalysisReport host similarity paging', () => {
  it('shows the first page of matches and a Load more button', () => {
    render(<AnalysisReport report={reportWithHostHits(36)} />)

    const card = screen.getByText('Host Similarity Evidence').closest('.evidence-host-similarity')

    expect(card.querySelectorAll('.host-hit')).toHaveLength(6)
    expect(within(card).getByText('Showing 6 of 36 matches')).toBeInTheDocument()
    expect(within(card).getByRole('button', { name: 'Load more' })).toBeInTheDocument()
    expect(within(card).queryByRole('button', { name: 'Show fewer' })).not.toBeInTheDocument()
  })

  it('loads another page each time and hides the button when everything is shown', () => {
    render(<AnalysisReport report={reportWithHostHits(14)} />)

    const card = screen.getByText('Host Similarity Evidence').closest('.evidence-host-similarity')

    fireEvent.click(within(card).getByRole('button', { name: 'Load more' }))
    expect(card.querySelectorAll('.host-hit')).toHaveLength(12)
    expect(within(card).getByText('Showing 12 of 14 matches')).toBeInTheDocument()

    fireEvent.click(within(card).getByRole('button', { name: 'Load more' }))
    expect(card.querySelectorAll('.host-hit')).toHaveLength(14)
    expect(within(card).getByText('Showing 14 of 14 matches')).toBeInTheDocument()
    expect(within(card).queryByRole('button', { name: 'Load more' })).not.toBeInTheDocument()

    fireEvent.click(within(card).getByRole('button', { name: 'Show fewer' }))
    expect(card.querySelectorAll('.host-hit')).toHaveLength(6)
  })

  it('has no paging controls when the matches fit on one page', () => {
    render(<AnalysisReport report={reportWithHostHits(4)} />)

    const card = screen.getByText('Host Similarity Evidence').closest('.evidence-host-similarity')

    expect(card.querySelectorAll('.host-hit')).toHaveLength(4)
    expect(within(card).queryByRole('button', { name: 'Load more' })).not.toBeInTheDocument()
  })

  it('formats host match numbers to two decimals', () => {
    render(<AnalysisReport report={reportWithHostHits(2)} />)

    const card = screen.getByText('Host Similarity Evidence').closest('.evidence-host-similarity')

    expect(within(card).getByText('Host Similarity: 20.00%')).toBeInTheDocument()
    expect(within(card).getByText('Host Similarity: 21.23%')).toBeInTheDocument()
    expect(within(card).getAllByText('41.67%')).toHaveLength(2)
    expect(within(card).getAllByText('1.23e-5')).toHaveLength(2)
  })
})

describe('AnalysisReport number formatting', () => {
  it('never prints a number with more than two decimals', () => {
    const { container } = render(<AnalysisReport report={reportWithHostHits(12)} />)

    // Check each element's own text so adjacent table cells are not
    // concatenated into false matches. Scientific e-values keep their exponent.
    const offenders = [...container.querySelectorAll('*')]
      .map((element) =>
        [...element.childNodes]
          .filter((node) => node.nodeType === Node.TEXT_NODE)
          .map((node) => node.textContent)
          .join(''),
      )
      .map((text) => text.replace(/\d\.\d+e-?\d+/g, ''))
      .filter((text) => /\d\.\d{3,}/.test(text))

    expect(offenders).toEqual([])
  })

  it('shows protein properties rounded to two decimals', () => {
    render(<AnalysisReport report={realReport} />)

    const value = (label) =>
      screen.getByText(label, { selector: 'dt' }).nextElementSibling

    expect(value('Molecular Weight')).toHaveTextContent('13,892.06')
    expect(value('GRAVY')).toHaveTextContent(/^-0\.12$/)
    expect(value('Isoelectric Point')).toHaveTextContent(/^9\.61$/)
  })

  it('reads net charge from the backend field name', () => {
    render(<AnalysisReport report={realReport} />)

    const card = screen.getByText('Net Charge').closest('.measurement-net-charge')

    expect(card.querySelector('p')).toHaveTextContent('+2.00')
  })
})
