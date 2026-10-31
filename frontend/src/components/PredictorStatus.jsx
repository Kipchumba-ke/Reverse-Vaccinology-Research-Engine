import './PredictorStatus.css'

// One row per optional external predictor. A predictor that is switched off,
// switched on but not set up, failed or finished is always shown, so a
// missing result is never a silent gap in the report.

const PREDICTORS = [
  {
    key: 'signalp',
    statusKey: 'signalp',
    name: 'SignalP 6.0',
    purpose: 'Signal peptide and cleavage site.',
  },
  {
    key: 'deeptmhmm',
    statusKey: 'deeptmhmm',
    name: 'DeepTMHMM',
    purpose: 'Transmembrane topology and protein class.',
  },
  {
    key: 'psortb',
    statusKey: 'psortb',
    name: 'PSORTb 3.0',
    purpose: 'Subcellular localization in bacteria.',
  },
  {
    key: 'epitopes',
    statusKey: 'iedb',
    name: 'IEDB',
    purpose: 'MHC binding and B-cell epitope predictions.',
  },
]

const STATE_LABELS = {
  completed: 'Completed',
  not_configured: 'Not set up',
  lookup_failed: 'Failed',
  not_performed: 'Not performed',
  not_enabled: 'Not enabled',
}

const STATE_MARKS = {
  completed: '✓',
  not_configured: '!',
  lookup_failed: '✕',
  not_performed: '–',
  not_enabled: '–',
}

function two(value) {
  return Number(value).toFixed(2)
}

function summarise(key, prediction) {
  if (!prediction) return ''

  if (key === 'signalp') {
    if (!prediction.detected) return 'No signal peptide predicted.'
    const type = prediction.signal_peptide_type ?? 'Signal peptide'
    return prediction.cleavage_after
      ? `${type}; cleavage after residue ${prediction.cleavage_after}.`
      : `${type}.`
  }

  if (key === 'deeptmhmm') {
    const helices = prediction.transmembrane_helices ?? 0
    const strands = prediction.beta_strands ?? 0
    const parts = [`Class ${prediction.predicted_class}`]
    if (helices) parts.push(`${helices} transmembrane helices`)
    if (strands) parts.push(`${strands} beta strands`)
    return `${parts.join('; ')}.`
  }

  if (key === 'psortb') {
    const score = Number(prediction.score)
    const note = score < 7.5 ? ', below the 7.50 confidence cut-off' : ''
    return `${prediction.localization}, score ${two(score)} of 10${note}.`
  }

  if (key === 'epitopes') {
    const mhcI = prediction.mhc_class_i?.binders?.length ?? 0
    const mhcII = prediction.mhc_class_ii?.binders?.length ?? 0
    const bcell = prediction.b_cell?.regions?.length ?? 0
    return `${mhcI} MHC-I and ${mhcII} MHC-II binder windows; ${bcell} B-cell regions.`
  }

  return ''
}

function stateFor(statusEntry, prediction) {
  const state = statusEntry?.status ?? prediction?.status
  return state && STATE_LABELS[state] ? state : 'not_enabled'
}

// Shown only for reports that carry sequence predictions, so reports saved
// before these analyses existed render exactly as they did.
function PredictorStatus({ report }) {
  if (!report?.measurements?.sequence_predictions) return null

  const predictions = report.measurements.sequence_predictions
  const statuses = report?.prediction_status ?? {}

  return (
    <section className="analysis-report-section predictor-status">
      <h3>Prediction Tools</h3>
      <p className="section-sub">
        Which optional external predictors ran for this report, and why any did not.
      </p>

      <ul className="predictor-list">
        {PREDICTORS.map((predictor) => {
          const prediction = predictions[predictor.key]
          const statusEntry = statuses[predictor.statusKey]
          const state = stateFor(statusEntry, prediction)
          const message = statusEntry?.message ?? prediction?.message
          const detail =
            state === 'completed'
              ? summarise(predictor.key, prediction)
              : state === 'not_enabled'
                ? 'Not enabled on this server.'
                : message

          return (
            <li key={predictor.key} className="predictor-row">
              <div className="predictor-name">
                <h4>{predictor.name}</h4>
                <p>{predictor.purpose}</p>
              </div>
              <p className={`predictor-state predictor-${state.replace('_', '-')}`}>
                <span aria-hidden="true">{STATE_MARKS[state]}</span>{' '}
                {STATE_LABELS[state]}
              </p>
              <p className="predictor-detail">{detail}</p>
            </li>
          )
        })}
      </ul>
    </section>
  )
}

export default PredictorStatus
