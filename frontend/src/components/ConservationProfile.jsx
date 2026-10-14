
 // Scientific note: this profile measures the frequency of the majority
 // residue at each alignment column. It is not Shannon entropy or an
 // evolutionary conservation score.

function calculateConservation(alignment) {
  if (!Array.isArray(alignment) || alignment.length === 0) {
    return []
  }

  const sequences = alignment.filter(
    (sequence) => typeof sequence === 'string',
  )

  if (sequences.length === 0) return []

  const width = Math.max(...sequences.map((sequence) => sequence.length))

  return Array.from({ length: width }, (_, index) => {
    const residues = sequences
      .map((sequence) => sequence[index])
      .filter((residue) => residue && residue !== '-')

    if (residues.length === 0) {
      return {
        position: index + 1,
        percentage: null,
        residueCount: 0,
        majorityResidue: null,
      }
    }

    const counts = residues.reduce((result, residue) => {
      result[residue] = (result[residue] ?? 0) + 1
      return result
    }, {})

    const majorityResidue = Object.keys(counts).reduce((best, residue) =>
      counts[residue] > counts[best] ? residue : best,
    )

    return {
      position: index + 1,
      percentage: (counts[majorityResidue] / residues.length) * 100,
      residueCount: residues.length,
      majorityResidue,
    }
  })
}

function ConservationProfile({ alignment }) {
  const positions = calculateConservation(alignment)
  const validPositions = positions.filter(
    (point) => point.percentage !== null,
  )

  if (positions.length === 0 || validPositions.length === 0) {
    return (
      <div className="conservation-profile-container">
        <p>No per-position conservation data is available.</p>
      </div>
    )
  }

  const chartWidth = 1000
  const chartHeight = 340
  const leftPadding = 64
  const rightPadding = 24
  const topPadding = 30
  const bottomPadding = 58

  const plotWidth = chartWidth - leftPadding - rightPadding
  const plotHeight = chartHeight - topPadding - bottomPadding

  const xForPosition = (position) =>
    leftPadding +
    ((position - 1) / Math.max(positions.length - 1, 1)) * plotWidth

  const yForPercentage = (percentage) =>
    topPadding + (1 - percentage / 100) * plotHeight

 
  const tickCount = Math.min(6, positions.length)
  const tickPositions = Array.from(
    { length: tickCount },
    (_, index) =>
      tickCount === 1
        ? 1
        : Math.round(
            1 + (index * (positions.length - 1)) / (tickCount - 1),
          ),
  ).filter((position, index, ticks) => ticks.indexOf(position) === index)

  const segments = []
  let currentSegment = []

  positions.forEach((point) => {
    if (point.percentage === null) {
      if (currentSegment.length) segments.push(currentSegment)
      currentSegment = []
      return
    }

    currentSegment.push({
      ...point,
      x: xForPosition(point.position),
      y: yForPercentage(point.percentage),
    })
  })

  if (currentSegment.length) segments.push(currentSegment)

  const overallMean =
    validPositions.reduce((sum, point) => sum + point.percentage, 0) /
    validPositions.length

  const stronglyConservedCount = validPositions.filter(
    (point) => point.percentage >= 80,
  ).length

  return (
    <div className="conservation-profile-container">
      <div className="conservation-profile-summary">
        <div className="conservation-profile-stat">
          <span className="conservation-profile-stat-label">
            Alignment positions
          </span>
          <strong>{positions.length.toLocaleString()}</strong>
        </div>

        <div className="conservation-profile-stat">
          <span className="conservation-profile-stat-label">
            Positions plotted
          </span>
          <strong>{validPositions.length.toLocaleString()}</strong>
        </div>

        <div className="conservation-profile-stat">
          <span className="conservation-profile-stat-label">
            Mean majority-residue frequency
          </span>
          <strong>{overallMean.toFixed(2)}%</strong>
        </div>

        <div className="conservation-profile-stat">
          <span className="conservation-profile-stat-label">
            Positions at 80% or above
          </span>
          <strong>{stronglyConservedCount.toLocaleString()}</strong>
        </div>
      </div>

      <div className="conservation-profile-chart-scroll">
        <svg
          className="conservation-profile"
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          role="img"
          aria-label="Per-position conservation profile"
          preserveAspectRatio="xMidYMid meet"
        >
          {[0, 25, 50, 75, 100].map((percentage) => {
            const y = yForPercentage(percentage)

            return (
              <g key={percentage}>
                <line
                  x1={leftPadding}
                  y1={y}
                  x2={chartWidth - rightPadding}
                  y2={y}
                  className={
                    percentage === 80
                      ? 'conservation-grid-line conservation-reference-line'
                      : 'conservation-grid-line'
                  }
                />
                <text
                  x={leftPadding - 12}
                  y={y + 4}
                  textAnchor="end"
                  className="conservation-axis-label"
                >
                  {percentage}%
                </text>
              </g>
            )
          })}

          {segments.map((segment, index) => {
            const path = segment
              .map(
                (point, pointIndex) =>
                  `${pointIndex === 0 ? 'M' : 'L'} ${point.x} ${point.y}`,
              )
              .join(' ')

            return (
              <path
                key={index}
                d={path}
                className="conservation-profile-line"
              />
            )
          })}

          {validPositions.map((point) => {
            // Avoid rendering hundreds of overlapping markers on long MSAs.
            if (positions.length > 150) return null

            const x = xForPosition(point.position)
            const y = yForPercentage(point.percentage)

            return (
              <circle
                key={point.position}
                cx={x}
                cy={y}
                r="3"
                className="conservation-profile-point"
              >
                <title>
                  Position {point.position}: {point.percentage.toFixed(2)}%
                  {'; '}majority residue: {point.majorityResidue}
                  {'; '}{point.residueCount} non-gap residues
                </title>
              </circle>
            )
          })}

          {positions
            .filter((point) => point.percentage === null)
            .map((point) => (
              <line
                key={`gap-${point.position}`}
                x1={xForPosition(point.position)}
                y1={topPadding + plotHeight + 3}
                x2={xForPosition(point.position)}
                y2={topPadding + plotHeight + 9}
                className="conservation-gap-marker"
              >
                <title>
                  Position {point.position}: all sequences contain gaps
                </title>
              </line>
            ))}

          {tickPositions.map((position) => {
            const x = xForPosition(position)

            return (
              <g key={position}>
                <line
                  x1={x}
                  y1={topPadding + plotHeight}
                  x2={x}
                  y2={topPadding + plotHeight + 5}
                  className="conservation-grid-line"
                />
                <text
                  x={x}
                  y={topPadding + plotHeight + 22}
                  textAnchor="middle"
                  className="conservation-axis-label"
                >
                  {position.toLocaleString()}
                </text>
              </g>
            )
          })}

          <text
            x={leftPadding + plotWidth / 2}
            y={chartHeight - 12}
            textAnchor="middle"
            className="conservation-axis-title"
          >
            Alignment position (residue column)
          </text>

          <text
            x="17"
            y={topPadding + plotHeight / 2}
            textAnchor="middle"
            transform={`rotate(-90 17 ${topPadding + plotHeight / 2})`}
            className="conservation-axis-title"
          >
            Majority-residue frequency (%)
          </text>
        </svg>
      </div>

      <p className="conservation-profile-note">
        Each value is the percentage of non-gap residues matching the most
        frequent residue in that alignment column. This is majority-residue
        frequency, not Shannon entropy or a standalone evolutionary
        conservation score. Columns containing only gaps are omitted from
        the profile and marked along the baseline.
      </p>
    </div>
  )
}

export default ConservationProfile
