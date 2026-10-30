import { describe, it, expect } from 'vitest'
import { annotationColorAt, buildTracks } from '../../utils/trackData'
import { makeReport } from '../fixtures/sequenceReport'

describe('buildTracks', () => {
  it('builds a track for every available prediction', () => {
    const { length, tracks } = buildTracks(makeReport())

    expect(length).toBe(100)
    expect(tracks.map((t) => t.id)).toEqual([
      'signal',
      'transmembrane',
      'antigenic',
      'bcell',
      'mhc1',
    ])
  })

  it('keeps only regions still classed as transmembrane after revision', () => {
    const track = buildTracks(makeReport()).tracks.find((t) => t.id === 'transmembrane')

    expect(track.segments).toHaveLength(1)
    expect(track.segments[0]).toMatchObject({ start: 60, end: 80 })
  })

  it('draws the signal peptide from the first residue to the cleavage site', () => {
    const track = buildTracks(makeReport()).tracks.find((t) => t.id === 'signal')

    expect(track.segments[0]).toMatchObject({ start: 1, end: 22 })
  })

  it('weights MHC binders by the number of alleles', () => {
    const track = buildTracks(makeReport()).tracks.find((t) => t.id === 'mhc1')

    expect(track.segments[0].weight).toBe(2)
  })

  it('omits MHC class II when it has no binders', () => {
    expect(buildTracks(makeReport()).tracks.some((t) => t.id === 'mhc2')).toBe(false)
  })

  it('leaves out epitope tracks when the IEDB lookup did not complete', () => {
    const report = makeReport()
    report.measurements.sequence_predictions.epitopes = { status: 'lookup_failed' }

    const ids = buildTracks(report).tracks.map((t) => t.id)

    expect(ids).not.toContain('bcell')
    expect(ids).not.toContain('mhc1')
  })

  it('adds DeepTMHMM segments when that prediction completed', () => {
    const report = makeReport()
    report.measurements.sequence_predictions.deeptmhmm = {
      status: 'completed',
      predicted_class: 'TM',
      segments: [{ type: 'transmembrane_helix', start: 10, end: 30 }],
    }

    const track = buildTracks(report).tracks.find((t) => t.id === 'deeptmhmm')

    expect(track.label).toContain('TM')
    expect(track.segments[0].label).toContain('Transmembrane helix')
  })

  it('ignores malformed regions', () => {
    const report = makeReport()
    report.measurements.sequence_predictions.antigenic_regions.regions = [
      { start: 'x', end: 4 },
      { start: 9, end: 3 },
    ]

    expect(buildTracks(report).tracks.some((t) => t.id === 'antigenic')).toBe(false)
  })

  it('copes with a report that has no predictions', () => {
    expect(buildTracks({})).toEqual({ length: 0, tracks: [] })
  })
})

describe('annotationColorAt', () => {
  it('returns the colour of the first covering track', () => {
    const { tracks } = buildTracks(makeReport())

    expect(annotationColorAt(10, tracks)).toBe(tracks[0].color)
    expect(annotationColorAt(70, tracks)).toBe(
      tracks.find((t) => t.id === 'transmembrane').color,
    )
  })

  it('returns null for uncovered residues', () => {
    expect(annotationColorAt(95, buildTracks(makeReport()).tracks)).toBeNull()
  })
})
