import { useMemo, useState } from 'react'
import ZoomFigure from './ZoomFigure'
import { formatNumber } from '../utils/format'
import './ReportFigures.css'

const WIDTH = 1000
const HEIGHT = 280
const PADDING = { top: 24, right: 30, bottom: 48, left: 60 }
const MIN_HYDROPATHY = -4.5
const MAX_HYDROPATHY = 4.5
const PLOT_WIDTH = WIDTH - PADDING.left - PADDING.right
const PLOT_HEIGHT = HEIGHT - PADDING.top - PADDING.bottom

function yForValue(value) {
  return (
    PADDING.top +
    (1 - (value - MIN_HYDROPATHY) / (MAX_HYDROPATHY - MIN_HYDROPATHY)) *
      PLOT_HEIGHT
  )
}

/**
 * Kyte–Doolittle sliding-window profile. Zoomable, with a hover/touch readout
 * that reports the window under the pointer.
 */
function HydropathyChart({ profile, sequenceLength }) {
  const [activeIndex, setActiveIndex] = useState(null)

  const points = useMemo(
    () =>
      profile
        .map((point) => {
          const value = Number(point.hydropathy)
          const start = Number(point.start)
          const end = Number(point.end)

          if (
            !Number.isFinite(value) ||
            !Number.isFinite(start) ||
            !Number.isFinite(end) ||
            start < 1 ||
            end < start
          ) {
            return null
          }

          const position = (start + end) / 2
          const x =
            PADDING.left +
            (profile.length === 1
              ? PLOT_WIDTH / 2
              : ((position - 1) / Math.max(1, sequenceLength - 1)) * PLOT_WIDTH)

          return {
            x,
            y: Math.max(
              PADDING.top,
              Math.min(HEIGHT - PADDING.bottom, yForValue(value)),
            ),
            position,
            value,
            start,
            end,
          }
        })
        .filter(Boolean),
    [profile, sequenceLength],
  )

  const zeroY = yForValue(0)
  const active = activeIndex == null ? null : points[activeIndex]

  function onPointerMove(event) {
    const rect = event.currentTarget.getBoundingClientRect()
    if (!rect.width || points.length === 0) return

    const x = ((event.clientX - rect.left) / rect.width) * WIDTH
    let best = 0
    let bestDistance = Infinity

    points.forEach((point, index) => {
      const distance = Math.abs(point.x - x)
      if (distance < bestDistance) {
        best = index
        bestDistance = distance
      }
    })

    setActiveIndex(best)
  }

  const ticks = Number.isFinite(sequenceLength) && sequenceLength > 0
    ? [0, 0.25, 0.5, 0.75, 1].map((fraction) => ({
        fraction,
        x: PADDING.left + fraction * PLOT_WIDTH,
        position: Math.round(fraction * (sequenceLength - 1)) + 1,
      }))
    : []

  return (
    <div className="hydropathy-chart-container">
      <ZoomFigure label="Hydropathy profile">
        <svg
          className="hydropathy-chart"
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          role="img"
          aria-label="Hydropathy profile chart"
          onPointerMove={onPointerMove}
          onPointerLeave={() => setActiveIndex(null)}
        >
          {ticks.map(({ fraction, x, position }) => (
            <g key={fraction}>
              <line
                x1={x}
                y1={HEIGHT - PADDING.bottom}
                x2={x}
                y2={HEIGHT - PADDING.bottom + 5}
                className="hydropathy-grid-line"
              />
              <text
                x={x}
                y={HEIGHT - PADDING.bottom + 19}
                textAnchor="middle"
                className="hydropathy-axis-label"
              >
                {position}
              </text>
            </g>
          ))}

          <text
            x={WIDTH / 2}
            y={HEIGHT - 8}
            textAnchor="middle"
            className="hydropathy-axis-label"
          >
            Residue position (window midpoint)
          </text>

          {[-4, -2, 0, 2, 4].map((value) => {
            const y = yForValue(value)

            return (
              <g key={value}>
                <line
                  x1={PADDING.left}
                  y1={y}
                  x2={WIDTH - PADDING.right}
                  y2={y}
                  className="hydropathy-grid-line"
                />
                <text
                  x={PADDING.left - 10}
                  y={y + 4}
                  textAnchor="end"
                  className="hydropathy-axis-label"
                >
                  {value}
                </text>
              </g>
            )
          })}

          <text
            x={PADDING.left}
            y={PADDING.top - 8}
            className="hydropathy-axis-label"
          >
            Hydropathy score
          </text>

          <line
            x1={PADDING.left}
            y1={zeroY}
            x2={WIDTH - PADDING.right}
            y2={zeroY}
            className="hydropathy-zero-line"
          />

          {points.length > 1 && (
            <polyline
              points={points.map((point) => `${point.x},${point.y}`).join(' ')}
              className="hydropathy-line"
            />
          )}

          {points.length === 1 && (
            <circle
              cx={points[0].x}
              cy={points[0].y}
              r="5"
              className="hydropathy-point"
            />
          )}

          {active && (
            <g className="hydropathy-cursor" pointerEvents="none">
              <line
                x1={active.x}
                x2={active.x}
                y1={PADDING.top}
                y2={HEIGHT - PADDING.bottom}
              />
              <circle cx={active.x} cy={active.y} r="6" />
            </g>
          )}
        </svg>
      </ZoomFigure>

      <p className="figure-readout" aria-live="polite">
        {active ? (
          <>
            Window <span className="num">{active.start}–{active.end}</span>
            {' · '}hydropathy <span className="num">{formatNumber(active.value)}</span>
            {' · '}
            {active.value > 1.6
              ? 'hydrophobic (possible membrane-spanning stretch)'
              : active.value < -1.6
                ? 'hydrophilic (likely solvent-exposed)'
                : 'intermediate'}
          </>
        ) : (
          'Move the pointer over the plot to read a window.'
        )}
      </p>
    </div>
  )
}

export default HydropathyChart
