import { annotationColorAt } from './trackData'

// AlphaFold's standard pLDDT colours.
export const PLDDT_BANDS = [
  { min: 90, color: '#0053D6', label: 'Very high (> 90)' },
  { min: 70, color: '#65CBF3', label: 'High (70-90)' },
  { min: 50, color: '#FFDB13', label: 'Low (50-70)' },
  { min: -Infinity, color: '#FF7D45', label: 'Very low (< 50)' },
]

export function plddtColor(plddt) {
  return PLDDT_BANDS.find((band) => plddt > band.min)?.color ?? PLDDT_BANDS.at(-1).color
}

export const NEUTRAL = '#9AA5B1'

export function residueColor(point, mode, tracks) {
  if (mode === 'confidence') return plddtColor(point.plddt)
  if (mode === 'annotation') return annotationColorAt(point.position, tracks) ?? NEUTRAL
  return NEUTRAL
}
