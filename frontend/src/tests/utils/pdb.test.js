import { describe, it, expect } from 'vitest'
import {
  centre,
  nearestPoint,
  parseCaTrace,
  project,
  sequenceOfTrace,
} from '../../utils/pdb'
import { plddtColor, residueColor, NEUTRAL } from '../../utils/structureColors'
import { SAMPLE_PDB } from '../fixtures/sequenceReport'

describe('parseCaTrace', () => {
  it('reads one point per C-alpha atom', () => {
    const points = parseCaTrace(SAMPLE_PDB)

    expect(points).toHaveLength(3)
    expect(points[0]).toMatchObject({ position: 1, residue: 'MET', x: 1, y: 0, z: 0, plddt: 95 })
    expect(points[2].plddt).toBeCloseTo(41.2)
  })

  it('ignores other atoms, TER lines and junk', () => {
    expect(parseCaTrace('TER\nREMARK x\nATOM  garbage')).toEqual([])
    expect(parseCaTrace(undefined)).toEqual([])
  })

  it('spells the sequence in one-letter codes', () => {
    expect(sequenceOfTrace(parseCaTrace(SAMPLE_PDB))).toBe('MKT')
  })
})

describe('centre', () => {
  it('moves the centroid to the origin and reports the radius', () => {
    const { points, radius } = centre(parseCaTrace(SAMPLE_PDB))

    const mean = (k) => points.reduce((s, p) => s + p[k], 0) / points.length
    expect(mean('x')).toBeCloseTo(0)
    expect(mean('y')).toBeCloseTo(0)
    expect(mean('z')).toBeCloseTo(0)
    expect(radius).toBeGreaterThan(0)
  })

  it('handles an empty trace', () => {
    expect(centre([])).toEqual({ points: [], radius: 1 })
  })
})

describe('project', () => {
  const points = [{ position: 1, residue: 'MET', plddt: 90, x: 10, y: 0, z: 0 }]

  it('maps the origin to the middle of the view', () => {
    const [p] = project([{ ...points[0], x: 0 }], {
      scale: 5, width: 200, height: 100,
    })

    expect([p.sx, p.sy]).toEqual([100, 50])
  })

  it('scales x with no rotation', () => {
    const [p] = project(points, { scale: 2, width: 200, height: 100 })

    expect(p.sx).toBeCloseTo(120)
    expect(p.sy).toBeCloseTo(50)
  })

  it('a quarter turn about y swings x into depth', () => {
    const [p] = project(points, {
      rotY: Math.PI / 2, scale: 1, width: 200, height: 100,
    })

    expect(p.sx).toBeCloseTo(100)
    expect(Math.abs(p.depth)).toBeCloseTo(10)
  })

  it('preserves distance from the centre under rotation', () => {
    const [p] = project(points, {
      rotX: 0.7, rotY: 1.1, scale: 1, width: 0, height: 0,
    })

    expect(Math.hypot(p.sx, p.sy, p.depth)).toBeCloseTo(10)
  })
})

describe('nearestPoint', () => {
  const projected = [
    { position: 1, sx: 10, sy: 10, depth: 0 },
    { position: 2, sx: 50, sy: 50, depth: 0 },
  ]

  it('finds the closest point within range', () => {
    expect(nearestPoint(projected, 12, 11).position).toBe(1)
  })

  it('returns null when nothing is close', () => {
    expect(nearestPoint(projected, 200, 200)).toBeNull()
  })
})

describe('colours', () => {
  it('uses the AlphaFold confidence bands', () => {
    expect(plddtColor(95)).toBe('#0053D6')
    expect(plddtColor(80)).toBe('#65CBF3')
    expect(plddtColor(60)).toBe('#FFDB13')
    expect(plddtColor(30)).toBe('#FF7D45')
  })

  it('treats the band edges as AlphaFold does', () => {
    expect(plddtColor(90)).toBe('#65CBF3')
    expect(plddtColor(70)).toBe('#FFDB13')
    expect(plddtColor(50)).toBe('#FF7D45')
  })

  it('falls back to neutral for plain mode and uncovered residues', () => {
    expect(residueColor({ plddt: 99, position: 1 }, 'plain', [])).toBe(NEUTRAL)
    expect(residueColor({ plddt: 99, position: 1 }, 'annotation', [])).toBe(NEUTRAL)
  })
})
