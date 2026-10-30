/**
 * Number formatting helpers for the analysis report.
 *
 * Every floating-point value shown in the report goes through these so it is
 * displayed with exactly two decimal places. Counts, residue positions and
 * lengths are integers and are rendered as-is.
 */

const UNAVAILABLE = 'Unavailable'

function toFiniteNumber(value) {
  if (value === null || value === undefined || value === '') return null
  const number = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(number) ? number : null
}

/** Fixed-point formatting: 43573.359879999996 -> "43573.36". */
export function formatNumber(value, { digits = 2, group = false, fallback = UNAVAILABLE } = {}) {
  const number = toFiniteNumber(value)
  if (number === null) return fallback
  if (group) {
    return number.toLocaleString('en-US', {
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    })
  }
  // Avoid "-0.00" for tiny negative values.
  const text = number.toFixed(digits)
  return Number(text) === 0 ? (0).toFixed(digits) : text
}

/** Percentage with two decimals: 11.616161 -> "11.62%". */
export function formatPercent(value, options = {}) {
  const text = formatNumber(value, { ...options, fallback: null })
  return text === null ? (options.fallback ?? UNAVAILABLE) : `${text}%`
}

/** Signed value for charges: 1.5 -> "+1.50", -0.2 -> "-0.20". */
export function formatSigned(value, options = {}) {
  const number = toFiniteNumber(value)
  if (number === null) return options.fallback ?? UNAVAILABLE
  const text = formatNumber(number, options)
  return number > 0 && !text.startsWith('-') ? `+${text}` : text
}

/**
 * BLAST e-values span many orders of magnitude, so very small values use
 * scientific notation with two decimals in the mantissa ("1.20e-5").
 */
export function formatEvalue(value, { fallback = UNAVAILABLE } = {}) {
  const number = toFiniteNumber(value)
  if (number === null) return fallback
  if (number === 0) return '0.00'
  if (Math.abs(number) < 0.01 || Math.abs(number) >= 1e5) {
    return number.toExponential(2)
  }
  return formatNumber(number)
}
