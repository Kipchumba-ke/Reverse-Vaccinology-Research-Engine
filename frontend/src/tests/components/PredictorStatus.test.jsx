import { describe, it, expect } from 'vitest'
import { render, screen, within } from '@testing-library/react'
import PredictorStatus from '../../components/PredictorStatus'

function report(predictions = {}, statuses) {
  return {
    measurements: { sequence_predictions: predictions },
    ...(statuses ? { prediction_status: statuses } : {}),
  }
}

function rowFor(name) {
  return screen.getByRole('heading', { name }).closest('li')
}

describe('PredictorStatus', () => {
  it('shows every predictor as not enabled when none was attempted', () => {
    render(<PredictorStatus report={report()} />)

    expect(screen.getByRole('heading', { name: 'Prediction Tools' })).toBeInTheDocument()

    for (const name of ['SignalP 6.0', 'DeepTMHMM', 'PSORTb 3.0', 'IEDB']) {
      const row = rowFor(name)
      expect(within(row).getByText(/Not enabled$/)).toBeInTheDocument()
      expect(within(row).getByText('Not enabled on this server.')).toBeInTheDocument()
    }
  })

  it('explains a predictor that is switched on but not set up', () => {
    render(
      <PredictorStatus
        report={report(
          { signalp: { status: 'not_configured', message: 'No signalp6 install was found.' } },
          { signalp: { status: 'not_configured', message: 'No signalp6 install was found.' } },
        )}
      />,
    )

    const row = rowFor('SignalP 6.0')
    expect(within(row).getByText(/Not set up/)).toBeInTheDocument()
    expect(within(row).getByText('No signalp6 install was found.')).toBeInTheDocument()
  })

  it('shows the reason a predictor failed', () => {
    render(
      <PredictorStatus
        report={report(
          { epitopes: { status: 'lookup_failed', message: 'IEDB request failed: timeout' } },
          { iedb: { status: 'lookup_failed', message: 'IEDB request failed: timeout' } },
        )}
      />,
    )

    const row = rowFor('IEDB')
    expect(within(row).getByText(/Failed/)).toBeInTheDocument()
    expect(within(row).getByText('IEDB request failed: timeout')).toBeInTheDocument()
  })

  it('summarises completed predictors', () => {
    render(
      <PredictorStatus
        report={report(
          {
            signalp: {
              status: 'completed',
              detected: true,
              signal_peptide_type: 'Sec/SPI (standard secretory signal peptide)',
              cleavage_after: 22,
            },
            deeptmhmm: {
              status: 'completed',
              predicted_class: 'TM',
              transmembrane_helices: 3,
              beta_strands: 0,
            },
            psortb: {
              status: 'completed',
              localization: 'CytoplasmicMembrane',
              score: 9.82,
            },
            epitopes: {
              status: 'completed',
              mhc_class_i: { binders: [{}, {}] },
              mhc_class_ii: { binders: [{}] },
              b_cell: { regions: [{}, {}, {}] },
            },
          },
          {
            signalp: { status: 'completed' },
            deeptmhmm: { status: 'completed' },
            psortb: { status: 'completed' },
            iedb: { status: 'completed' },
          },
        )}
      />,
    )

    expect(
      within(rowFor('SignalP 6.0')).getByText(/cleavage after residue 22/),
    ).toBeInTheDocument()
    expect(
      within(rowFor('DeepTMHMM')).getByText('Class TM; 3 transmembrane helices.'),
    ).toBeInTheDocument()
    expect(
      within(rowFor('PSORTb 3.0')).getByText('CytoplasmicMembrane, score 9.82 of 10.'),
    ).toBeInTheDocument()
    expect(
      within(rowFor('IEDB')).getByText('2 MHC-I and 1 MHC-II binder windows; 3 B-cell regions.'),
    ).toBeInTheDocument()
  })

  it('states when PSORTb is below its confidence cut-off', () => {
    render(
      <PredictorStatus
        report={report(
          { psortb: { status: 'completed', localization: 'Unknown', score: 2 } },
          { psortb: { status: 'completed' } },
        )}
      />,
    )

    expect(
      within(rowFor('PSORTb 3.0')).getByText(/below the 7\.50 confidence cut-off/),
    ).toBeInTheDocument()
  })

  it('renders nothing for reports saved before predictions existed', () => {
    const { container } = render(<PredictorStatus report={{ measurements: {} }} />)

    expect(container).toBeEmptyDOMElement()
  })
})
