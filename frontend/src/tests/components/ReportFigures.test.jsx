import { describe, it, expect } from 'vitest'
import { fireEvent, render, screen } from '@testing-library/react'
import HydropathyChart from '../../components/HydropathyChart'
import TransmembraneMap from '../../components/TransmembraneMap'
import AnalysisReport from '../../components/AnalysisReport'
import realReport from '../fixtures/realReport.json'

describe('HydropathyChart', () => {
  const profile = [
    { start: 1, end: 9, hydropathy: 2.123 },
    { start: 2, end: 10, hydropathy: -2.5 },
  ]

  it('is wrapped in zoom controls', () => {
    render(<HydropathyChart profile={profile} sequenceLength={10} />)

    expect(
      screen.getByRole('button', { name: /zoom in hydropathy profile/i }),
    ).toBeInTheDocument()
  })

  it('shows a prompt until a window is read', () => {
    render(<HydropathyChart profile={profile} sequenceLength={10} />)

    expect(screen.getByText(/move the pointer over the plot/i)).toBeInTheDocument()
  })

  it('reports the window under the pointer with two decimals', () => {
    render(<HydropathyChart profile={profile} sequenceLength={10} />)

    const svg = screen.getByRole('img', { name: /hydropathy profile chart/i })
    svg.getBoundingClientRect = () => ({ left: 0, top: 0, width: 1000, height: 280 })

    fireEvent.pointerMove(svg, { clientX: 70, clientY: 100 })

    expect(screen.getByText(/window/i, { selector: '.figure-readout' })).toHaveTextContent(
      /1–9.*2\.12/,
    )
  })
})

describe('TransmembraneMap', () => {
  const candidates = [
    { start: 5, end: 25 },
    { start: 40, end: 60 },
  ]

  it('describes a region on hover and on focus', () => {
    render(<TransmembraneMap candidates={candidates} sequenceLength={100} />)

    const region = screen.getByLabelText('Candidate region from residue 5 to 25')

    fireEvent.pointerEnter(region)
    expect(screen.getByText(/region 1 of 2: residues 5 to 25/i)).toBeInTheDocument()

    fireEvent.pointerLeave(region)
    expect(screen.getByText(/hover or focus a region/i)).toBeInTheDocument()

    fireEvent.focus(screen.getByLabelText('Candidate region from residue 40 to 60'))
    expect(screen.getByText(/region 2 of 2: residues 40 to 60/i)).toBeInTheDocument()
  })
})

describe('host similarity cards', () => {
  function reportWithHit() {
    const report = structuredClone(realReport)
    report.evidence.host_similarity = [
      {
        host_id: 'sp|P12345|HOST_HUMAN',
        identity_percentage: 31.4159,
        alignment_length: 90,
        query_coverage_percentage: 62.5,
        subject_coverage_percentage: 48.125,
        e_value: 0.5,
        source: 'BLASTP',
        confidence: 'medium',
      },
    ]
    return report
  }

  it('shows the host ID with query and subject coverage', () => {
    render(<AnalysisReport report={reportWithHit()} />)

    expect(screen.getByText('sp|P12345|HOST_HUMAN')).toBeInTheDocument()
    expect(screen.getByText('Query coverage', { selector: 'dt' }).nextElementSibling).toHaveTextContent('62.50%')
    expect(screen.getByText('Subject coverage', { selector: 'dt' }).nextElementSibling).toHaveTextContent('48.13%')
  })

  it('draws a bar for identity and each coverage, scaled to the value', () => {
    const { container } = render(<AnalysisReport report={reportWithHit()} />)
    const card = container.querySelector('.host-hit')
    const widths = [...card.querySelectorAll('.meter-fill')].map((el) => el.style.width)

    expect(widths).toEqual(['31.4159%', '62.5%', '48.125%'])
    card.querySelectorAll('.meter').forEach((meter) =>
      expect(meter).toHaveAttribute('aria-hidden', 'true'),
    )
  })
})
