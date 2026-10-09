import { useState } from "react";

function AnalysisReport({ report }) {
  const [showAllPeptides, setShowAllPeptides] = useState(false);

  const peptideCandidates = report.peptide_candidates ?? [];
  const visiblePeptides = showAllPeptides
    ? peptideCandidates
    : peptideCandidates.slice(0, 10);
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

        <div className="measurement-net-charge measurement-card">
          <h4>Net Charge</h4>
          <p>
            {report.measurements?.charge_and_hydrophobicity?.net_charge}
          </p>
        </div>

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

        <div className="measurement-hydropathy measurement-card">
          <h4>Hydropathy Profile</h4>

          {(() => {
            const profile = report.measurements?.hydropathy_profile ?? [];

            if (profile.length === 0) {
              return <p>No hydropathy profile is available.</p>;
            }

            const width = 1000;
            const height = 240;
            const padding = 24;
            const minHydropathy = -4.5;
            const maxHydropathy = 4.5;
            const plotWidth = width - padding * 2;
            const plotHeight = height - padding * 2;

            const points = profile
              .map((point, index) => {
                const x =
                  padding +
                  (profile.length === 1
                    ? plotWidth / 2
                    : (index / (profile.length - 1)) * plotWidth);

                const value = Number(point.hydropathy);
                const normalized =
                  (value - minHydropathy) /
                  (maxHydropathy - minHydropathy);

                const y = padding + (1 - normalized) * plotHeight;

                return {
                  x,
                  y: Math.max(padding, Math.min(height - padding, y)),
                };
              })
              .filter((point) => Number.isFinite(point.x) && Number.isFinite(point.y));

            const zeroY =
              padding +
              (1 - (0 - minHydropathy) / (maxHydropathy - minHydropathy)) *
                plotHeight;

            return (
              <>
                <p>{profile.length} sliding windows</p>

                <div className="hydropathy-chart-container">
                  <svg
                    className="hydropathy-chart"
                    viewBox={`0 0 ${width} ${height}`}
                    role="img"
                    aria-label="Hydropathy profile chart"
                  >
                    <line
                      x1={padding}
                      y1={zeroY}
                      x2={width - padding}
                      y2={zeroY}
                      className="hydropathy-zero-line"
                    />

                    {points.length > 1 && (
                      <polyline
                        points={points.map((point) => `${point.x},${point.y}`).join(' ')}
                        className="hydropathy-line"
                      />
                    )}

                    {points.length === 1 && (
                      <circle
                        cx={points[0].x}
                        cy={points[0].y}
                        r="5"
                        className="hydropathy-point"
                      />
                    )}
                  </svg>
                </div>

                <details className="hydropathy-raw-data">
                  <summary>Raw hydropathy values</summary>

                  <div className="hydropathy-table-container">
                    <table>
                      <thead>
                        <tr>
                          <th>Start</th>
                          <th>End</th>
                          <th>Hydropathy</th>
                        </tr>
                      </thead>
                      <tbody>
                        {profile.map((point, index) => (
                          <tr key={`${point.start}-${point.end}-${index}`}>
                            <td>{point.start}</td>
                            <td>{point.end}</td>
                            <td>
                              {Number.isFinite(Number(point.hydropathy))
                                ? Number(point.hydropathy).toFixed(3)
                                : 'Unavailable'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </details>
              </>
            );
          })()}
        </div>

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
          <div className="conservation-summary measurement-card">
            <h4>Conservation Summary</h4>

            <div className="measurement-values">
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
            </div>
          </div>
        )}

        {report.conservation?.regions?.length > 0 && (
          <div className="conserved-regions measurement-card">
            <h4>Conserved Regions</h4>

            <div className="measurement-values">
              {report.conservation.regions.map(
                (region, index) => (
                  <p key={index}>
                    Conserved Region: {region.start}-{region.end}
                  </p>
                ),
              )}
            </div>
          </div>
        )}


        {!report.conservation?.summary &&
          !(report.conservation?.regions?.length > 0) && (
            <p className="report-unavailable-message">
              Conservation results are unavailable because no comparative sequence alignment was provided.
            </p>
          )}
      </section>

      <section className="analysis-report-section">
        <h3>Evidence</h3>

        {report.evidence?.localization?.length > 0 && (
          <div className="evidence-localization evidence-card">
            <h4>Localization Evidence</h4>

            <div className="evidence-values">
              {report.evidence.localization.map(
                (evidence, index) => (
                  <div key={index}>
                    <p>Localization: {evidence.location}</p>
                    <p>Source: {evidence.source}</p>
                    <p>Confidence: {evidence.confidence}</p>
                  </div>
                ),
              )}
            </div>
          </div>
        )}

        {report.evidence?.essentiality?.length > 0 && (
          <div className="evidence-essentiality evidence-card">
            <h4>Essentiality Evidence</h4>

            <div className="evidence-values">
              {report.evidence.essentiality.map(
                (evidence, index) => (
                  <div key={index}>
                    <p>Essentiality: {evidence.evidence}</p>
                    <p>Source: {evidence.source}</p>
                    <p>Confidence: {evidence.confidence}</p>
                  </div>
                ),
              )}
            </div>
          </div>
        )}

        {report.evidence?.host_similarity?.length > 0 && (
          <div className="evidence-host-similarity evidence-card">
            <h4>Host Similarity Evidence</h4>

            <div className="evidence-values">
              {report.evidence.host_similarity.map(
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
                    <p>
                      Source: {evidence.source}
                    </p>
                    <p>
                      Confidence: {evidence.confidence}
                    </p>
                  </div>
                ),
              )}
            </div>
          </div>
        )}


        {!report.evidence?.localization?.length &&
          !report.evidence?.essentiality?.length &&
          !report.evidence?.host_similarity?.length && (
            <p className="report-unavailable-message">
              No localization, essentiality, or host similarity evidence was provided for this report.
            </p>
          )}
      </section>

      <section className="analysis-report-section">

        <h3>Interpretations</h3>

        {report.interpretations?.length > 0 && (
          <div className="interpretations-list">
            {report.interpretations.map(
              (interpretation, index) => (
                <div
                  key={index}
                  className="interpretation-card"
                >
                  <p className="interpretation-text">
                    {interpretation.interpretation}
                  </p>
                  <p>Category: {interpretation.category}</p>
                  <p>Confidence: {interpretation.confidence}</p>
                </div>
              ),
            )}
          </div>
        )}
      </section>

      
      <section className="analysis-report-section">
        <h3>Candidate Assessment</h3>

        {report.candidate_assessment && (
          <div className="candidate-assessment-card">
            <div className="candidate-assessment-summary">
              <div>
                <span className="candidate-assessment-label">
                  Assessment Status
                </span>
                <p>
                  {report.candidate_assessment.status
                    ?.replaceAll('_', ' ') || 'Not available'}
                </p>
              </div>
            </div>

            <div className="candidate-assessment-rationale">
              <span className="candidate-assessment-label">
                Rationale
              </span>
              <p>
                {report.candidate_assessment.rationale ||
                  'No assessment rationale provided.'}
              </p>
            </div>

            {report.candidate_assessment.supporting_evidence?.length > 0 && (
              <div className="candidate-assessment-evidence">
                <h4>Supporting Evidence</h4>
                <ul>
                  {report.candidate_assessment.supporting_evidence.map(
                    (item, index) => (
                      <li key={`support-${index}`}>{item}</li>
                    ),
                  )}
                </ul>
              </div>
            )}

            {report.candidate_assessment.concerns?.length > 0 && (
              <div className="candidate-assessment-concerns">
                <h4>Concerns</h4>
                <ul>
                  {report.candidate_assessment.concerns.map(
                    (item, index) => (
                      <li key={`concern-${index}`}>{item}</li>
                    ),
                  )}
                </ul>
              </div>
            )}

            {report.candidate_assessment.missing_evidence?.length > 0 && (
              <div className="candidate-assessment-missing-evidence">
                <h4>Missing Evidence</h4>
                <ul>
                  {report.candidate_assessment.missing_evidence.map(
                    (item, index) => (
                      <li key={`missing-${index}`}>{item}</li>
                    ),
                  )}
                </ul>
              </div>
            )}
          </div>
        )}
      </section>


      <section className="analysis-report-section">
        <h3>Limitations</h3>

        {report.limitations?.length > 0 && (
          <div className="limitations-list">
            {report.limitations.map(
              (limitation, index) => (
                <div
                  key={index}
                  className="limitation-card"
                >
                  <p>{limitation}</p>
                </div>
              ),
            )}
          </div>
        )}
      </section>

      <section className="analysis-report-section">
        <h3>Peptide Candidates</h3>

        {peptideCandidates.length === 0 ? (
          <p>No peptide candidates are available.</p>
        ) : (
          <>
            <p className="peptide-candidate-count">
              {peptideCandidates.length} peptide candidates
            </p>

            <div
              className="peptide-candidates-list"
              data-testid="peptide-candidates-list"
            >
              {visiblePeptides.map((candidate, index) => (
                <div
                  key={`${candidate.start}-${candidate.end}-${index}`}
                  className="peptide-candidate-card"
                >
                  <div className="peptide-sequence">
                    <span className="peptide-candidate-label">
                      Peptide Candidate
                    </span>
                    <p>{candidate.sequence}</p>
                  </div>

                  <div className="peptide-candidate-details">
                    <div>
                      <span className="peptide-candidate-label">Position</span>
                      <p>
                        {candidate.start}-{candidate.end}
                      </p>
                    </div>

                    <div>
                      <span className="peptide-candidate-label">Length</span>
                      <p>{candidate.length}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {peptideCandidates.length > 10 && (
              <button
                type="button"
                className="peptide-candidates-toggle"
                onClick={() => setShowAllPeptides((previous) => !previous)}
              >
                {showAllPeptides
                  ? 'Show fewer peptide candidates'
                  : 'Show all peptide candidates'}
              </button>
            )}
          </>
        )}
      </section>
    </div>
  )
}

export default AnalysisReport