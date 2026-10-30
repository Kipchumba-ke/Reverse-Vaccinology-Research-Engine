import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MhcBindingMap from '../../components/MhcBindingMap'
import { makeReport } from '../fixtures/sequenceReport'

describe('MhcBindingMap', () => {
  it('draws one heatmap per class that has alleles', () => {
    render(<MhcBindingMap report={makeReport()} />)

    expect(
      screen.getByRole('img', { name: /MHC class I predicted binders/ }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('img', { name: /MHC class II predicted binders/ }),
    ).toBeInTheDocument()
  })

  it('shades cells with the best rank in their window', () => {
    render(<MhcBindingMap report={makeReport()} />)

    const chart = screen.getByRole('img', { name: /MHC class I predicted binders/ })
    const titles = [...chart.querySelectorAll('rect title')].map((t) => t.textContent)

    expect(titles.some((t) => /HLA-A\*02:01/.test(t) && /0\.2/.test(t))).toBe(true)
  })

  it('lists the most promiscuous peptides', () => {
    render(<MhcBindingMap report={makeReport()} />)

    expect(screen.getByText('LLLALLLAL')).toBeInTheDocument()
  })

  it('states that an empty cell is not proof of non-binding', () => {
    render(<MhcBindingMap report={makeReport()} />)

    expect(screen.getAllByText(/not proof of non-binding/).length).toBeGreaterThan(0)
  })

  it('mentions B-cell regions that contain binders', () => {
    render(<MhcBindingMap report={makeReport()} />)

    expect(screen.getByText(/also contain MHC binders/)).toBeInTheDocument()
  })

  it('renders nothing when the IEDB lookup did not complete', () => {
    const report = makeReport()
    report.measurements.sequence_predictions.epitopes = { status: 'lookup_failed' }

    const { container } = render(<MhcBindingMap report={report} />)

    expect(container).toBeEmptyDOMElement()
  })
})
