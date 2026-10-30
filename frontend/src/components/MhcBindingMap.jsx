import { formatNumber } from '../utils/format'

const WIDTH = 1000
const LEFT = 150
const RIGHT = 20
const ROW = 22
const TOP = 10
const MAX_BINS = 120

// Lower percentile rank means stronger predicted binding.
function shade(rank, cutoff) {
  const strength = 1 - Math.min(Math.max(rank / cutoff, 0), 1)
  return 0.25 + 0.75 * strength
}

function buildRows(binders, length, bins) {
  const binSize = Math.ceil(length / bins)
  const rows = new Map()

  for (const binder of binders) {
    for (const hit of binder.alleles ?? []) {
      if (!hit.allele) continue
      const cells = rows.get(hit.allele) ?? new Map()

      for (
        let bin = Math.floor((binder.start - 1) / binSize);
        bin <= Math.floor((binder.end - 1) / binSize);
        bin += 1
      ) {
        const best = cells.get(bin)
        if (best === undefined || hit.percentile_rank < best) {
          cells.set(bin, hit.percentile_rank)
        }
      }
      rows.set(hit.allele, cells)
    }
  }

  return { rows, binSize }
}

function Heatmap({ title, data, length }) {
  const alleles = data?.alleles ?? []
  const binders = data?.binders ?? []
  const cutoff = data?.rank_cutoff ?? 1

  if (alleles.length === 0) return null

  const bins = Math.min(MAX_BINS, length)
  const { rows, binSize } = buildRows(binders, length, bins)
  const plotWidth = WIDTH - LEFT - RIGHT
  const cellWidth = plotWidth / Math.ceil(length / binSize)
  const height = TOP + alleles.length * ROW + 24

  return (
    <div className="mhc-map">
      <h4>{title}</h4>
      <svg
        viewBox={`0 0 ${WIDTH} ${height}`}
        role="img"
        aria-label={`${title} predicted binders by allele and position`}
        className="mhc-map-chart"
      >
        {alleles.map((allele, rowIndex) => {
          const y = TOP + rowIndex * ROW
          const cells = rows.get(allele) ?? new Map()
          const failed = Boolean(data.alleles_failed?.[allele])

          return (
            <g key={allele}>
              <text x={LEFT - 8} y={y + 14} textAnchor="end" className="mhc-map-label">
                {allele}
                {failed ? ' (failed)' : ''}
              </text>
              <rect x={LEFT} y={y + 2} width={plotWidth} height={ROW - 4} className="mhc-map-lane" />
              {[...cells.entries()].map(([bin, rank]) => (
                <rect
                  key={bin}
                  x={LEFT + bin * cellWidth}
                  y={y + 2}
                  width={Math.max(cellWidth, 1.5)}
                  height={ROW - 4}
                  fill="#332288"
                  fillOpacity={shade(rank, cutoff)}
                >
                  <title>
                    {allele}, residues {bin * binSize + 1}-{Math.min((bin + 1) * binSize, length)}:
                    best percentile rank {formatNumber(rank)}
                  </title>
                </rect>
              ))}
            </g>
          )
        })}

        <text x={LEFT} y={height - 6} className="mhc-map-tick">1</text>
        <text x={LEFT + plotWidth} y={height - 6} textAnchor="end" className="mhc-map-tick">
          {length}
        </text>
      </svg>
      <p className="mhc-map-note">
        Shaded cells mark peptides at or below the percentile-rank cut-off of {cutoff}
        ; darker means stronger predicted binding. An empty cell means no predicted
        binder at that cut-off, not proof of non-binding.
      </p>
    </div>
  )
}

function MhcBindingMap({ report }) {
  const epitopes = report?.measurements?.sequence_predictions?.epitopes
  const length = report?.protein?.length ?? report?.protein?.sequence?.length ?? 0

  if (epitopes?.status !== 'completed' || !length) return null

  const top = [...(epitopes.mhc_class_i?.binders ?? [])].slice(0, 5)

  return (
    <div className="mhc-binding">
      <Heatmap title="MHC class I" data={epitopes.mhc_class_i} length={length} />
      <Heatmap title="MHC class II" data={epitopes.mhc_class_ii} length={length} />

      {top.length > 0 && (
        <div className="mhc-top">
          <h4>Most promiscuous MHC class I peptides</h4>
          <table>
            <thead>
              <tr>
                <th>Peptide</th>
                <th>Positions</th>
                <th>Alleles</th>
                <th>Best rank</th>
              </tr>
            </thead>
            <tbody>
              {top.map((binder) => (
                <tr key={`${binder.start}-${binder.peptide}`}>
                  <td>{binder.peptide}</td>
                  <td>
                    {binder.start}-{binder.end}
                  </td>
                  <td>{binder.allele_count}</td>
                  <td>{formatNumber(binder.best_percentile_rank)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {epitopes.overlaps?.length > 0 && (
        <p className="mhc-overlaps">
          {epitopes.overlaps.length} predicted B-cell region(s) also contain MHC binders (
          {epitopes.overlaps.map((o) => `${o.start}-${o.end}`).join(', ')}).
        </p>
      )}
    </div>
  )
}

export default MhcBindingMap
