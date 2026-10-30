// Hand-built report fragment in the shape the backend produces.
export function makeReport(overrides = {}) {
  return {
    protein: {
      accession: 'P0A911',
      length: 100,
      sequence: 'M'.repeat(100),
    },
    measurements: {
      transmembrane_candidates: [
        {
          start: 5,
          end: 24,
          classification: 'candidate_transmembrane',
          revised_classification: 'signal_peptide_h_region',
        },
        {
          start: 60,
          end: 80,
          classification: 'candidate_transmembrane',
          revised_classification: 'candidate_transmembrane',
        },
      ],
      sequence_predictions: {
        signal_peptide: { detected: true, cleavage_after: 22, confidence: 'medium' },
        antigenic_regions: {
          regions: [{ start: 30, end: 45, mean_propensity: 1.05 }],
        },
        localization_hint: { hint: 'membrane_associated', confidence: 'low' },
        epitopes: {
          status: 'completed',
          b_cell: { regions: [{ start: 35, end: 50, mean_score: 0.8 }] },
          mhc_class_i: {
            alleles: ['HLA-A*02:01', 'HLA-A*01:01'],
            rank_cutoff: 1,
            alleles_failed: {},
            binders: [
              {
                peptide: 'LLLALLLAL',
                start: 36,
                end: 44,
                allele_count: 2,
                best_percentile_rank: 0.2,
                alleles: [
                  { allele: 'HLA-A*02:01', percentile_rank: 0.2 },
                  { allele: 'HLA-A*01:01', percentile_rank: 0.6 },
                ],
              },
            ],
          },
          mhc_class_ii: {
            alleles: ['HLA-DRB1*01:01'],
            rank_cutoff: 10,
            alleles_failed: {},
            binders: [],
          },
          overlaps: [{ start: 35, end: 50, mhc_i_binders: 1, mhc_ii_binders: 0 }],
        },
      },
    },
    ...overrides,
  }
}

export function pdbAtom(serial, name, residue, position, [x, y, z], plddt) {
  return (
    `ATOM  ${String(serial).padStart(5)} ${name.padStart(3).padEnd(4)} ` +
    `${residue.padEnd(3)} A${String(position).padStart(4)}    ` +
    `${x.toFixed(3).padStart(8)}${y.toFixed(3).padStart(8)}${z.toFixed(3).padStart(8)}` +
    `${(1).toFixed(2).padStart(6)}${plddt.toFixed(2).padStart(6)}           C`
  )
}

export const SAMPLE_PDB = [
  pdbAtom(1, 'N', 'MET', 1, [0, 0, 0], 95),
  pdbAtom(2, 'CA', 'MET', 1, [1, 0, 0], 95),
  pdbAtom(3, 'CA', 'LYS', 2, [2, 1, 0], 72.5),
  pdbAtom(4, 'CA', 'THR', 3, [3, 1, 1], 41.2),
  'TER',
].join('\n')
