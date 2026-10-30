import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import SequenceInsights from '../../components/SequenceInsights'
import AnalysisReport from '../../components/AnalysisReport'
import { makeReport } from '../fixtures/sequenceReport'
import realReport from '../fixtures/realReport.json'

describe('SequenceInsights', () => {
  it('renders the map, heatmaps and structure panel for new reports', () => {
    render(<SequenceInsights report={makeReport()} />)

    expect(screen.getByRole('heading', { name: 'Sequence Map and Structure' })).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'Sequence feature map' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Load predicted 3-D structure' })).toBeInTheDocument()
  })

  it('renders nothing for reports saved before these predictions existed', () => {
    const report = makeReport()
    delete report.measurements.sequence_predictions

    const { container } = render(<SequenceInsights report={report} />)

    expect(container).toBeEmptyDOMElement()
  })

  it('appears inside the analysis report for new reports only', () => {
    // realReport.json was produced by the backend report code, with the
    // IEDB service replaced by sample responses.
    const newReport = structuredClone(realReport)
    const oldReport = structuredClone(realReport)
    delete oldReport.measurements.sequence_predictions

    const { unmount } = render(<AnalysisReport report={newReport} />)
    expect(screen.getByText('Sequence Map and Structure')).toBeInTheDocument()
    unmount()

    render(<AnalysisReport report={oldReport} />)
    expect(screen.queryByText('Sequence Map and Structure')).not.toBeInTheDocument()
  })
})

describe('SequenceInsights with a backend-shaped report', () => {
  it('draws tracks and heatmaps from real report fields', () => {
    render(<SequenceInsights report={structuredClone(realReport)} />)

    expect(screen.getByRole('img', { name: 'Sequence feature map' })).toBeInTheDocument()
    expect(
      screen.getByRole('img', { name: /MHC class I predicted binders/ }),
    ).toBeInTheDocument()
  })
})
