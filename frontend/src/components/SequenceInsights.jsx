import './SequenceInsights.css'
import MhcBindingMap from './MhcBindingMap'
import SequenceTracks from './SequenceTracks'
import StructureViewer from './StructureViewer'
import { buildTracks } from '../utils/trackData'

// Shown only for reports that carry sequence predictions, so reports saved
// before these analyses existed render exactly as they did.
function SequenceInsights({ report }) {
  if (!report?.measurements?.sequence_predictions) return null

  const { tracks } = buildTracks(report)

  return (
    <section className="analysis-report-section sequence-insights">
      <h3>Sequence Map and Structure</h3>

      <SequenceTracks report={report} />
      <MhcBindingMap report={report} />

      <div className="sequence-insights-structure">
        <h4>Predicted 3-D structure</h4>
        <StructureViewer
          accession={report.protein?.accession ?? ''}
          sequence={report.protein?.sequence ?? ''}
          tracks={tracks}
        />
      </div>
    </section>
  )
}

export default SequenceInsights
