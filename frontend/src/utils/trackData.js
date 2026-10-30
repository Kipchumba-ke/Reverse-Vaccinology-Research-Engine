// Turns a report into the tracks drawn on the sequence map.
//
// Every region here is in sequence coordinates (1-based, inclusive).
// Conserved regions are left out on purpose: the report gives them in
// alignment columns, which stop matching sequence positions once gaps are
// inserted.
import { formatNumber } from './format.js'


export const TRACK_COLORS = {
  signal: '#0072B2',
  transmembrane: '#D55E00',
  hydrophobic: '#E69F00',
  antigenic: '#009E73',
  bcell: '#CC79A7',
  mhc1: '#56B4E9',
  mhc2: '#332288',
}

function regions(list, labelFor) {
  return (Array.isArray(list) ? list : [])
    .filter(
      (item) =>
        Number.isFinite(item?.start) &&
        Number.isFinite(item?.end) &&
        item.end >= item.start,
    )
    .map((item) => ({
      start: item.start,
      end: item.end,
      label: labelFor(item),
      weight: item.weight ?? 1,
    }))
}

function track(id, label, color, source, segments) {
  return { id, label, color, source, segments }
}

export function buildTracks(report) {
  const predictions = report?.measurements?.sequence_predictions ?? {}
  const length = report?.protein?.length ?? report?.protein?.sequence?.length ?? 0
  const tracks = []

  const signal = predictions.signal_peptide
  const signalp = predictions.signalp
  const signalSegments = []

  if (signal?.detected && signal.cleavage_after) {
    signalSegments.push({
      start: 1,
      end: signal.cleavage_after,
      label: `Signal peptide, cleavage after ${signal.cleavage_after} (${signal.confidence ?? 'unrated'} confidence)`,
      weight: 1,
    })
  }

  if (signalSegments.length) {
    tracks.push(
      track(
        'signal',
        'Signal peptide (ReverseVax rules)',
        TRACK_COLORS.signal,
        'heuristic',
        signalSegments,
      ),
    )
  }

  if (signalp?.status === 'completed' && signalp.detected && signalp.cleavage_after) {
    tracks.push(
      track('signalp', 'Signal peptide (SignalP 6.0)', TRACK_COLORS.signal, 'SignalP 6.0', [
        {
          start: 1,
          end: signalp.cleavage_after,
          label: `${signalp.signal_peptide_type ?? 'Signal peptide'}, cleavage after ${signalp.cleavage_after}`,
          weight: 1,
        },
      ]),
    )
  }

  const candidates = report?.measurements?.transmembrane_candidates ?? []
  const effective = (item) => item.revised_classification ?? item.classification

  const transmembrane = regions(
    candidates.filter((item) => effective(item) === 'candidate_transmembrane'),
    (item) => `Transmembrane candidate ${item.start}-${item.end}`,
  )

  if (transmembrane.length) {
    tracks.push(
      track(
        'transmembrane',
        'Transmembrane candidates (heuristic)',
        TRACK_COLORS.transmembrane,
        'heuristic',
        transmembrane,
      ),
    )
  }

  const deeptmhmm = predictions.deeptmhmm
  if (deeptmhmm?.status === 'completed') {
    const labels = {
      transmembrane_helix: 'Transmembrane helix',
      beta_strand: 'Beta strand',
      signal_peptide: 'Signal peptide',
    }
    const segments = regions(
      deeptmhmm.segments,
      (item) => `${labels[item.type] ?? item.type} ${item.start}-${item.end}`,
    )

    if (segments.length) {
      tracks.push(
        track(
          'deeptmhmm',
          `Topology (DeepTMHMM: ${deeptmhmm.predicted_class})`,
          TRACK_COLORS.transmembrane,
          'DeepTMHMM',
          segments,
        ),
      )
    }
  }

  const antigenic = regions(
    predictions.antigenic_regions?.regions,
    (item) => `Antigenic region ${item.start}-${item.end} (mean propensity ${formatNumber(item.mean_propensity)})`,
  )

  if (antigenic.length) {
    tracks.push(
      track(
        'antigenic',
        'Antigenic propensity (Kolaskar-Tongaonkar)',
        TRACK_COLORS.antigenic,
        'heuristic',
        antigenic,
      ),
    )
  }

  const epitopes = predictions.epitopes
  if (epitopes?.status === 'completed') {
    const bcell = regions(
      epitopes.b_cell?.regions,
      (item) => `B-cell epitope region ${item.start}-${item.end} (mean score ${formatNumber(item.mean_score)})`,
    )

    if (bcell.length) {
      tracks.push(
        track('bcell', 'B-cell epitopes (IEDB Bepipred-2.0)', TRACK_COLORS.bcell, 'IEDB', bcell),
      )
    }

    const binders = (list) =>
      regions(
        (list ?? []).map((item) => ({ ...item, weight: item.allele_count })),
        (item) =>
          `${item.peptide} ${item.start}-${item.end}: binds ${item.allele_count} allele(s), best rank ${item.best_percentile_rank}`,
      )

    const mhc1 = binders(epitopes.mhc_class_i?.binders)
    if (mhc1.length) {
      tracks.push(track('mhc1', 'MHC class I binders (IEDB)', TRACK_COLORS.mhc1, 'IEDB', mhc1))
    }

    const mhc2 = binders(epitopes.mhc_class_ii?.binders)
    if (mhc2.length) {
      tracks.push(track('mhc2', 'MHC class II binders (IEDB)', TRACK_COLORS.mhc2, 'IEDB', mhc2))
    }
  }

  return { length, tracks }
}

// Colour a residue by the first track that covers it, in track order.
export function annotationColorAt(position, tracks) {
  for (const item of tracks) {
    if (item.segments.some((s) => position >= s.start && position <= s.end)) {
      return item.color
    }
  }
  return null
}
