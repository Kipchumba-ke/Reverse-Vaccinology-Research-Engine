import { buildTracks } from '../utils/trackData'

const WIDTH = 1000
const LEFT = 300
const RIGHT = 20
const ROW = 26
const TOP = 12
const AXIS = 30

function ticksFor(length) {
  const count = Math.min(6, length)
  const ticks = Array.from({ length: count }, (_, index) =>
    count === 1 ? 1 : Math.round(1 + (index * (length - 1)) / (count - 1)),
  )
  return ticks.filter((tick, index) => ticks.indexOf(tick) === index)
}

function SequenceTracks({ report }) {
  const { length, tracks } = buildTracks(report)

  if (!length || tracks.length === 0) {
    return (
      <p className="sequence-tracks-empty">
        No signal peptide, topology or epitope features were found to draw.
      </p>
    )
  }

  const plotWidth = WIDTH - LEFT - RIGHT
  const x = (position) => LEFT + ((position - 1) / Math.max(length - 1, 1)) * plotWidth
  const height = TOP + tracks.length * ROW + AXIS

  return (
    <div className="sequence-tracks">
      <svg
        viewBox={`0 0 ${WIDTH} ${height}`}
        role="img"
        aria-label="Sequence feature map"
        className="sequence-tracks-chart"
      >
        {tracks.map((track, index) => {
          const y = TOP + index * ROW

          return (
            <g key={track.id}>
              <text x={LEFT - 10} y={y + 15} textAnchor="end" className="sequence-tracks-label">
                {track.label}
              </text>
              <rect
                x={LEFT}
                y={y + 4}
                width={plotWidth}
                height={14}
                className="sequence-tracks-lane"
              />
              {track.segments.map((segment, segmentIndex) => (
                <rect
                  key={`${segment.start}-${segment.end}-${segmentIndex}`}
                  x={x(segment.start)}
                  y={y + 4}
                  width={Math.max(x(segment.end) - x(segment.start), 2)}
                  height={14}
                  fill={track.color}
                  fillOpacity={Math.min(1, 0.35 + 0.2 * segment.weight)}
                >
                  <title>{segment.label}</title>
                </rect>
              ))}
            </g>
          )
        })}

        <g transform={`translate(0 ${TOP + tracks.length * ROW + 4})`}>
          <line x1={LEFT} x2={LEFT + plotWidth} y1={0} y2={0} className="sequence-tracks-axis" />
          {ticksFor(length).map((tick) => (
            <g key={tick}>
              <line x1={x(tick)} x2={x(tick)} y1={0} y2={5} className="sequence-tracks-axis" />
              <text x={x(tick)} y={19} textAnchor="middle" className="sequence-tracks-tick">
                {tick}
              </text>
            </g>
          ))}
        </g>
      </svg>

      <details className="sequence-tracks-text">
        <summary>Show the same features as text</summary>
        <ul>
          {tracks.map((track) => (
            <li key={track.id}>
              <strong>{track.label}</strong>:{' '}
              {track.segments.map((s) => `${s.start}-${s.end}`).join(', ')}
            </li>
          ))}
        </ul>
      </details>

      <p className="sequence-tracks-note">
        Regions are in sequence positions. Rule-based tracks are screens written
        for this project, not SignalP, TMHMM or BepiPred output.
      </p>
    </div>
  )
}

export default SequenceTracks
