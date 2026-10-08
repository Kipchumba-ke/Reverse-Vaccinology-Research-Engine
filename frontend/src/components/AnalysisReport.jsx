function AnalysisReport({ report }) {
  return (
    <div className="analysis-report">
      <h2>Analysis Report</h2>

      
      <div className="report-overview">
        {report.metadata && (
          <section className="analysis-report-section">
            <h3>Report Metadata</h3>
            <p>
              Report Type: {report.metadata.report_type}
            </p>
            <p>
              Report Version: {report.metadata.report_version}
            </p>
            <p>
              Analysis Pipeline: {report.metadata.analysis_pipeline}
            </p>
          </section>
        )}

        <section className="analysis-report-section">
          <h3>Protein Characteristics</h3>

          <div className="protein-characteristics-grid">
            <p>Protein ID: {report.protein?.id}</p>
            <p>Name: {report.protein?.name}</p>
            <p>Organism: {report.protein?.organism}</p>
            <p>Accession: {report.protein?.accession}</p>
            <p>Length: {report.protein?.length}</p>
            <p>Molecular Weight: {report.protein?.molecular_weight}</p>
            <p>GRAVY: {report.protein?.gravy}</p>
            <p>Isoelectric Point: {report.protein?.isoelectric_point}</p>
          </div>
          <div className="protein-sequence">
            <strong>Sequence</strong>
            <p>{report.protein?.sequence}</p>
          </div>
        </section>
      </div>

      <section className="analysis-report-section">
        <h3>Measurements</h3>

        <p>
          Net Charge:{' '}
          {report.measurements?.charge_and_hydrophobicity?.net_charge}
        </p>

        {report.measurements?.composition && (
          <div className="measurement-composition measurement-card">

            <h4>Composition</h4>

            <p>
              Composition Length:{' '}
              {report.measurements.composition.length}
            </p>

            {Object.entries(
              report.measurements.composition.counts || {},
            ).map(([aminoAcid, count]) => (
              <p key={`count-${aminoAcid}`}>
                Composition Count: {aminoAcid} {count}
              </p>
            ))}

            {Object.entries(
              report.measurements.composition.percentages || {},
            ).map(([aminoAcid, percentage]) => (
              <p key={`percentage-${aminoAcid}`}>
                Composition Percentage: {aminoAcid} {percentage}%
              </p>
            ))}
          </div>
        )}

        {report.measurements?.hydropathy_profile?.length > 0 && (
          <div className="measurement-hydropathy measurement-card">
            <h4>Hydropathy Profile</h4>

            <div className="measurement-values">
              {report.measurements.hydropathy_profile.map(
                (point, index) => (
                  <p key={index}>
                    Hydropathy: Position {point.position}, Value {point.value}
                  </p>
                ),
              )}
            </div>
          </div>
        )}

        {report.measurements?.hydrophobic_regions?.length > 0 && (
          <div className="measurement-hydrophobic-regions measurement-card">
            <h4>Hydrophobic Regions</h4>

            <div className="measurement-values">
              {report.measurements.hydrophobic_regions.map(
                (region, index) => (
                  <p key={index}>
                    Hydrophobic Region: {region.start}-{region.end}
                  </p>
                ),
              )}
            </div>
          </div>
        )}

        {report.measurements?.transmembrane_candidates?.length > 0 && (
          <div className="measurement-transmembrane measurement-card">
            <h4>Transmembrane Candidates</h4>

            <div className="measurement-values">
              {report.measurements.transmembrane_candidates.map(
                (candidate, index) => (
                  <p key={index}>
                    Transmembrane Candidate: {candidate.start}-{candidate.end}
                  </p>
                ),
              )}
            </div>
          </div>
        )}
      </section>

      <section className="analysis-report-section">
        <h3>Conservation</h3>

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
      </section>

      <section className="analysis-report-section">
        <h3>Evidence</h3>

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
      </section>

      <section className="analysis-report-section">

        <h3>Interpretations</h3>

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
      </section>

      <section className="analysis-report-section">
        <h3>Candidate Assessment</h3>

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
      </section>

      <section className="analysis-report-section">
        <h3>Limitations</h3>

        {report.limitations?.map(
          (limitation, index) => (
            <p key={index}>
              {limitation}
            </p>
          ),
        )}
      </section>

      <section className="analysis-report-section">
        <h3>Peptide Candidates</h3>

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
      </section>
    </div>
  )
}

export default AnalysisReport