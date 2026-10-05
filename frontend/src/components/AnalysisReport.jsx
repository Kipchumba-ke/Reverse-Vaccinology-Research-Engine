function AnalysisReport({ report }) {
  return (
    <div>
      <h2>Analysis Report</h2>

      {report.metadata && (
        <>
          <p>
            Report Type: {report.metadata.report_type}
          </p>
          <p>
            Report Version: {report.metadata.report_version}
          </p>
          <p>
            Analysis Pipeline: {report.metadata.analysis_pipeline}
          </p>
        </>
      )}

      <p>Protein ID: {report.protein?.id}</p>
      <p>Name: {report.protein?.name}</p>
      <p>Organism: {report.protein?.organism}</p>
      <p>Accession: {report.protein?.accession}</p>
      <p>Sequence: {report.protein?.sequence}</p>
      <p>Length: {report.protein?.length}</p>
      <p>Molecular Weight: {report.protein?.molecular_weight}</p>
      <p>GRAVY: {report.protein?.gravy}</p>
      <p>Isoelectric Point: {report.protein?.isoelectric_point}</p>

      <p>
        Net Charge:{' '}
        {report.measurements?.charge_and_hydrophobicity?.net_charge}
      </p>

      {report.measurements?.composition &&
        Object.entries(report.measurements.composition).map(
          ([aminoAcid, value]) => (
            <p key={aminoAcid}>
              Composition: {aminoAcid} {value}
            </p>
          ),
        )}

      {report.measurements?.hydropathy_profile?.map(
        (point, index) => (
          <p key={index}>
            Hydropathy: Position {point.position}, Value {point.value}
          </p>
        ),
      )}

      {report.measurements?.hydrophobic_regions?.map(
        (region, index) => (
          <p key={index}>
            Hydrophobic Region: {region.start}-{region.end}
          </p>
        ),
      )}

      {report.measurements?.transmembrane_candidates?.map(
        (candidate, index) => (
          <p key={index}>
            Transmembrane Candidate: {candidate.start}-{candidate.end}
          </p>
        ),
      )}

      {report.conservation?.summary && (
        <>
          <p>
            Conservation:{' '}
            {report.conservation.summary.conservation_percentage}%
          </p>

          <p>
            Alignment Length:{' '}
            {report.conservation.summary.alignment_length}
          </p>

          <p>
            Sequences Analyzed:{' '}
            {report.conservation.summary.sequence_count}
          </p>
        </>
      )}

      {report.conservation?.regions?.map(
        (region, index) => (
          <p key={index}>
            Conserved Region: {region.start}-{region.end}
          </p>
        ),
      )}

      {report.evidence?.localization?.map(
        (evidence, index) => (
          <div key={index}>
            <p>
              Localization: {evidence.location}
            </p>
            <p>
              Source: {evidence.source}
            </p>
            <p>
              Confidence: {evidence.confidence}
            </p>
          </div>
        ),
      )}

      {report.evidence?.essentiality?.map(
        (evidence, index) => (
          <div key={index}>
            <p>Essentiality: {evidence.evidence}</p>
            <p>Source: {evidence.source}</p>
            <p>Confidence: {evidence.confidence}</p>
          </div>
        ),
      )}

      {report.evidence?.host_similarity?.map(
        (evidence, index) => (
          <div key={index}>
            <p>
              Host Similarity: {evidence.identity_percentage}%
            </p>
            <p>
              Alignment Length: {evidence.alignment_length}
            </p>
            <p>
              E-value: {evidence.e_value}
            </p>
            <p>Source: {evidence.source}</p>
            <p>Confidence: {evidence.confidence}</p>
          </div>
        ),
      )}

      {report.interpretations?.map(
        (interpretation, index) => (
          <div key={index}>
            <p>
              {interpretation.interpretation}
            </p>
            <p>
              Category: {interpretation.category}
            </p>
            <p>
              Confidence: {interpretation.confidence}
            </p>
          </div>
        ),
      )}

      {report.candidate_assessment && (
        <div>
          <p>
            Category: {report.candidate_assessment.category}
          </p>
          <p>
            Score: {report.candidate_assessment.score}
          </p>
          <p>
            {report.candidate_assessment.rationale}
          </p>
        </div>
      )}

      {report.limitations?.map(
        (limitation, index) => (
          <p key={index}>
            {limitation}
          </p>
        ),
      )}

      {report.peptide_candidates?.map(
        (candidate, index) => (
          <div key={index}>
            <p>
              Peptide Candidate: {candidate.sequence}
            </p>
            <p>
              Position: {candidate.start}-{candidate.end}
            </p>
            <p>
              Length: {candidate.length}
            </p>
          </div>
        ),
      )}
    </div>
  )
}

export default AnalysisReport