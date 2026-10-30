import { useState } from 'react'
import ZoomFigure from './ZoomFigure'
import './ReportFigures.css'

const WIDTH = 800
const HEIGHT = 120
const LEFT = 40
const RIGHT = 20
const PLOT_WIDTH = WIDTH - LEFT - RIGHT

/**
 * Region map of transmembrane candidates along the sequence. Zoomable; hovering
 * or focusing a region highlights it and reports its residues below the plot.
 */
function TransmembraneMap({ candidates, sequenceLength }) {
  const [active, setActive] = useState(null)

  return (
    <div className="transmembrane-map-container">
      <ZoomFigure label="Transmembrane region map">
        <svg
          className="transmembrane-region-map"
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          role="img"
          aria-label="Transmembrane region map"
        >
          <line
            x1={LEFT}
            y1="55"
            x2={WIDTH - RIGHT}
            y2="55"
            className="transmembrane-sequence-line"
          />

          {[0, 0.25, 0.5, 0.75, 1].map((fraction) => {
            const x = LEFT + fraction * PLOT_WIDTH
            const position = Math.round(fraction * sequenceLength)

            return (
              <g key={fraction}>
                <line
                  x1={x}
                  y1="45"
                  x2={x}
                  y2="70"
                  className="transmembrane-axis-tick"
                />
                <text
                  x={x}
                  y="88"
                  textAnchor="middle"
                  className="transmembrane-axis-label"
                >
                  {position}
                </text>
              </g>
            )
          })}

          {candidates.map((candidate, index) => {
            const start = Number(candidate.start)
            const end = Number(candidate.end)

            if (
              !Number.isFinite(start) ||
              !Number.isFinite(end) ||
              start < 1 ||
              end < start ||
              start > sequenceLength
            ) {
              return null
            }

            const boundedEnd = Math.min(end, sequenceLength)
            const x = LEFT + ((start - 1) / sequenceLength) * PLOT_WIDTH
            const regionWidth = Math.max(
              2,
              ((boundedEnd - start + 1) / sequenceLength) * PLOT_WIDTH,
            )

            return (
              <rect
                key={`${start}-${end}-${index}`}
                x={x}
                y="43"
                width={Math.min(regionWidth, WIDTH - RIGHT - x)}
                height="24"
                rx="2"
                className={`transmembrane-region${
                  active === index ? ' is-active' : ''
                }`}
                tabIndex={0}
                aria-label={`Candidate region from residue ${start} to ${end}`}
                onPointerEnter={() => setActive(index)}
                onPointerLeave={() => setActive(null)}
                onFocus={() => setActive(index)}
                onBlur={() => setActive(null)}
              >
                <title>
                  Candidate region: residues {start} to {end}
                </title>
              </rect>
            )
          })}

          <text
            x={WIDTH / 2}
            y="112"
            textAnchor="middle"
            className="transmembrane-axis-label"
          >
            Amino acid position
          </text>
        </svg>
      </ZoomFigure>

      <p className="figure-readout" aria-live="polite">
        {active != null && candidates[active]
          ? `Region ${active + 1} of ${candidates.length}: residues ${candidates[active].start} to ${candidates[active].end} (${
              Number(candidates[active].end) - Number(candidates[active].start) + 1
            } residues).`
          : 'Hover or focus a region to read its residues.'}
      </p>
    </div>
  )
}

export default TransmembraneMap
