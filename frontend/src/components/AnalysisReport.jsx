import { useState } from "react";
import SequenceInsights from "./SequenceInsights";
import PredictorStatus from "./PredictorStatus";
import HydropathyChart from "./HydropathyChart";
import TransmembraneMap from "./TransmembraneMap";
import {
  formatEvalue,
  formatNumber,
  formatPercent,
  formatSigned,
} from "../utils/format";

const HOST_SIMILARITY_PAGE_SIZE = 6;

/** Clamp a percentage to 0-100 for bar widths. */
function barWidth(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "0%";
  return `${Math.min(100, Math.max(0, number))}%`;
}

/** Decorative bar; the value is always also printed as text beside it. */
function Meter({ value }) {
  return (
    <span className="meter" aria-hidden="true">
      <span className="meter-fill" style={{ width: barWidth(value) }} />
    </span>
  );
}

function ConfidenceBadge({ confidence }) {
  if (!confidence) return null;
  const level = String(confidence).toLowerCase();

  return (
    <span className={`badge badge-confidence badge-${level.replace(/[^a-z]+/g, "-")}`}>
      Confidence: {confidence}
    </span>
  );
}

function AnalysisReport({ report, title = 'Analysis Report'  }) {
  const [showAllPeptides, setShowAllPeptides] = useState(false);
  const [showFullSequence, setShowFullSequence] = useState(false);
  const [visibleRegionCount, setVisibleRegionCount] = useState(10)
  const [visiblePeptideCount, setVisiblePeptideCount] = useState(10)
  const [visibleHostCount, setVisibleHostCount] = useState(
    HOST_SIMILARITY_PAGE_SIZE,
  )

  const maxComposition = Math.max(
    1e-9,
    ...Object.values(report.measurements?.composition?.percentages ?? {}).map(Number).filter(Number.isFinite),
  );

  const peptideCandidates = report.peptide_candidates ?? [];
  const visiblePeptides = showAllPeptides
    ? peptideCandidates
    : peptideCandidates.slice(0, 10);

  const proteinSequence = report.protein?.sequence ?? '';
  const sequencePreviewLength = 120;
  const isLongSequence = proteinSequence.length > sequencePreviewLength;

  const displayedSequence =
    isLongSequence && !showFullSequence
      ? `${proteinSequence.slice(0, sequencePreviewLength)}...`
      : proteinSequence;
  return (
    <div className="analysis-report">
      <h2>{title}</h2>

      
      <div className="report-overview">
        {report.metadata && (
          <section className="analysis-report-section">
            <h3>Report Metadata</h3>
            <p className="section-sub">Which version of the pipeline produced this report.</p>
            <dl className="stat-list stat-list-stack">
              <div className="stat">
                <dt>Report Type</dt>
                <dd>{report.metadata.report_type}</dd>
              </div>
              <div className="stat">
                <dt>Report Version</dt>
                <dd>{report.metadata.report_version}</dd>
              </div>
              <div className="stat">
                <dt>Analysis Pipeline</dt>
                <dd>{report.metadata.analysis_pipeline}</dd>
              </div>
            </dl>
          </section>
        )}

        <section className="analysis-report-section">
          <h3>Protein Characteristics</h3>
          <p className="section-sub">The sequence submitted and its basic physical properties.</p>

          <dl className="protein-characteristics-grid stat-list">
            <div className="stat">
              <dt>Protein ID</dt>
              <dd>{report.protein?.id}</dd>
            </div>
            <div className="stat">
              <dt>Name</dt>
              <dd>{report.protein?.name}</dd>
            </div>
            <div className="stat">
              <dt>Organism</dt>
              <dd>{report.protein?.organism}</dd>
            </div>
            <div className="stat">
              <dt>Accession</dt>
              <dd>{report.protein?.accession}</dd>
            </div>
            <div className="stat">
              <dt>Length</dt>
              <dd>{report.protein?.length}</dd>
            </div>
            <div className="stat">
              <dt>Molecular Weight</dt>
              <dd>
                {formatNumber(report.protein?.molecular_weight, { group: true, fallback: "" })}
                {report.protein?.molecular_weight != null && (
                  <span className="stat-unit"> Da</span>
                )}
              </dd>
            </div>
            <div className="stat">
              <dt>GRAVY</dt>
              <dd>{formatNumber(report.protein?.gravy, { fallback: "" })}</dd>
            </div>
            <div className="stat">
              <dt>Isoelectric Point</dt>
              <dd>
                {formatNumber(report.protein?.isoelectric_point, { fallback: "" })}
              </dd>
            </div>
          </dl>
          <div className="protein-sequence" data-testid="protein-sequence">
            <strong>Sequence ({proteinSequence.length} amino acids)</strong>
            <p>{displayedSequence}</p>

            {isLongSequence && (
              <button
                type="button"
                onClick={() => setShowFullSequence((current) => !current)}
              >
                {showFullSequence ? 'Show less' : 'Show full sequence'}
              </button>
            )}
          </div>
        </section>
      </div>

      <section className="analysis-report-section">
        <h3>Measurements</h3>
        <p className="section-sub">Charge, composition and hydropathy, computed from the sequence alone.</p>

        <div className="measurement-net-charge measurement-card">
          <h4>Net Charge</h4>
          <p>
            {formatSigned(
              report.measurements?.charge_and_hydrophobicity?.net_charge ??
                report.measurements?.charge_and_hydrophobicity
                  ?.approximate_net_charge,
              { fallback: "" },
            )}
          </p>
          {report.measurements?.charge_and_hydrophobicity && (
            <dl className="stat-list stat-list-compact">
              {[
                ["Positively charged", "positively_charged", "residues"],
                ["Negatively charged", "negatively_charged", "residues"],
                ["Hydrophobic residues", "hydrophobic_residues", "residues"],
              ].map(([label, key]) =>
                report.measurements.charge_and_hydrophobicity[key] != null ? (
                  <div className="stat" key={key}>
                    <dt>{label}</dt>
                    <dd>{report.measurements.charge_and_hydrophobicity[key]}</dd>
                  </div>
                ) : null,
              )}
              {report.measurements.charge_and_hydrophobicity
                .hydrophobicity_percentage != null && (
                <div className="stat">
                  <dt>Hydrophobicity</dt>
                  <dd>
                    {formatPercent(
                      report.measurements.charge_and_hydrophobicity
                        .hydrophobicity_percentage,
                    )}
                  </dd>
                </div>
              )}
            </dl>
          )}
        </div>

        {report.measurements?.composition && (
          <div className="measurement-composition measurement-card">
            <h4>Composition</h4>

            <p>
              Composition Length:{' '}
              {report.measurements.composition.length}
            </p>

            <div
              className="composition-table-container"
              tabIndex={0}
              role="region"
              aria-label="Amino acid composition, scrollable"
            >
              <table aria-label="Amino Acid Composition">
                <thead>
                  <tr>
                    <th scope="col">Amino Acid</th>
                    <th scope="col">Count</th>
                    <th scope="col">Percentage</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.from(
                    new Set([
                      ...Object.keys(
                        report.measurements.composition.counts ?? {},
                      ),
                      ...Object.keys(
                        report.measurements.composition.percentages ?? {},
                      ),
                    ]),
                  ).map((aminoAcid) => (
                    <tr key={aminoAcid}>
                      <td>{aminoAcid}</td>
                      <td>
                        {report.measurements.composition.counts?.[aminoAcid] ?? 'Unavailable'}
                      </td>
                      <td>
                        {report.measurements.composition.percentages?.[aminoAcid] != null
                          ? formatPercent(report.measurements.composition.percentages[aminoAcid])
                          : 'Unavailable'}
                        {report.measurements.composition.percentages?.[aminoAcid] != null && (
                          <Meter
                            value={(Number(report.measurements.composition.percentages[aminoAcid]) / maxComposition) * 100}
                          />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        <div className="measurement-hydropathy measurement-card">
          <h4>Hydropathy Profile</h4>

          {(() => {
            const profile = report.measurements?.hydropathy_profile ?? [];

            if (profile.length === 0) {
              return <p>No hydropathy profile is available.</p>;
            }

            const sequenceLength = Number(
              report.protein?.length || proteinSequence.length,
            );

            return (
              <>
                <p>{profile.length} sliding windows</p>

                <HydropathyChart
                  profile={profile}
                  sequenceLength={sequenceLength}
                />

                <details className="hydropathy-raw-data">
                  <summary>Raw hydropathy values</summary>

                  <div
                    className="hydropathy-table-container"
                    tabIndex={0}
                    role="region"
                    aria-label="Raw hydropathy values, scrollable"
                  >
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
                              {formatNumber(point.hydropathy)}
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

            {(() => {
              const sequenceLength = Number(
                report.protein?.length || proteinSequence.length,
              );

              if (!Number.isFinite(sequenceLength) || sequenceLength <= 0) {
                return (
                  <p>
                    A sequence length is required to display the region map.
                  </p>
                );
              }

              return (
                <TransmembraneMap
                  candidates={report.measurements.transmembrane_candidates}
                  sequenceLength={sequenceLength}
                />
              );
            })()}

            <div className="measurement-values">
              {report.measurements.transmembrane_candidates.map(
                (candidate, index) => (
                  <p key={`${candidate.start}-${candidate.end}-${index}`}>
                    Transmembrane Candidate: {candidate.start}-{candidate.end}
                  </p>
                ),
              )}
            </div>
          </div>
        )}

        {!(report.measurements?.transmembrane_candidates?.length > 0) && (
          <div className="measurement-transmembrane measurement-card">
            <h4>Transmembrane Candidates</h4>
            <p>
              No transmembrane candidates met the current heuristic
              criteria. This does not rule out membrane association.
            </p>
          </div>
        )}
      </section>

      <SequenceInsights report={report} />

      <PredictorStatus report={report} />

      <section className="analysis-report-section">
        <h3>Conservation</h3>
        <p className="section-sub">How much of the sequence is shared across the strains provided.</p>

        {report.conservation?.summary && (
          <div className="conservation-summary measurement-card">
            <h4>Conservation Summary</h4>

            <div className="measurement-values">
              <p>
                Conservation:{' '}
                {formatPercent(report.conservation.summary.conservation_percentage, { fallback: "Unavailable" })}
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

            <div
              className="report-table-wrapper conserved-regions-table-wrapper"
              tabIndex={0}
              role="region"
              aria-label="Conserved regions, scrollable"
            >
              <table className="report-table">
                <thead>
                  <tr>
                    <th>Region</th>
                    <th>Start</th>
                    <th>End</th>
                    <th>Length</th>
                    <th>Consensus</th>
                  </tr>
                </thead>

                <tbody>
                  {report.conservation.regions
                    .slice(0, visibleRegionCount)
                    .map((region, index) => (
                      <tr key={`${region.start}-${region.end}-${index}`}>
                        <td>{index + 1}</td>
                        <td>{region.start}</td>
                        <td>{region.end}</td>
                        <td>
                          {region.length ?? region.end - region.start + 1}
                        </td>
                        <td className="sequence-cell">
                          {region.consensus ??
                            region.sequence ??
                            "Not available"}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>

            {report.conservation.regions.length > 10 && (
              <div className="conserved-regions-controls">
                <span className="regions-count">
                  Showing {Math.min(
                    visibleRegionCount,
                    report.conservation.regions.length
                  )} of {report.conservation.regions.length} regions
                </span>

                {visibleRegionCount < report.conservation.regions.length ? (
                  <button
                    type="button"
                    className="conserved-regions-toggle"
                    onClick={() =>
                      setVisibleRegionCount((current) =>
                        Math.min(
                          current + 10,
                          report.conservation.regions.length
                        )
                      )
                    }
                  >
                    Show 10 more regions
                  </button>
                ) : (
                  <button
                    type="button"
                    className="conserved-regions-toggle"
                    onClick={() => setVisibleRegionCount(10)}
                  >
                    Show fewer regions
                  </button>
                )}
              </div>
            )}
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
        <p className="section-sub">Where the protein sits, whether it is essential, and how it compares with the host.</p>
        {report.evidence_status?.epath_essentiality && (
          <div className="evidence-epath-status evidence-card">
            <h4>ePath Essentiality Lookup</h4>
            <p>
              Status:{' '}
              <strong>
                {report.evidence_status.epath_essentiality.status}
              </strong>
            </p>
            <p>
              {report.evidence_status.epath_essentiality.message}
            </p>
          </div>
        )}

        {report.evidence?.localization?.length > 0 && (
          <div className="evidence-localization evidence-card">
            <h4>Localization Evidence</h4>

            <div className="evidence-values">
              {report.evidence.localization.map(
                (evidence, index) => (
                  <div key={index} className="evidence-item">
                    <p className="evidence-item-title">Localization: {evidence.location}</p>
                    <p className="evidence-item-meta">
                      <span>Source: {evidence.source}</span>
                      <ConfidenceBadge confidence={evidence.confidence} />
                    </p>
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
                  <div key={index} className="evidence-item">
                    <p className="evidence-item-title">Essentiality: {evidence.evidence}</p>
                    <p className="evidence-item-meta">
                      <span>Source: {evidence.source}</span>
                      <ConfidenceBadge confidence={evidence.confidence} />
                    </p>
                  </div>
                ),
              )}
            </div>
          </div>
        )}

        {report.evidence?.host_similarity?.length > 0 && (() => {
          const hits = report.evidence.host_similarity;
          const shown = Math.min(visibleHostCount, hits.length);

          return (
            <div className="evidence-host-similarity evidence-card">
              <h4>Host Similarity Evidence</h4>

              <div className="evidence-values host-similarity-grid">
                {hits.slice(0, visibleHostCount).map((evidence, index) => (
                  <div key={index} className="evidence-item host-hit">
                    <p className="host-hit-id">
                      <span className="host-hit-label">Host ID</span>
                      <span className="host-hit-value num">
                        {evidence.host_id ?? "Not reported"}
                      </span>
                    </p>
                    <p className="evidence-item-title">
                      Host Similarity: {formatPercent(evidence.identity_percentage)}
                    </p>
                    <Meter value={evidence.identity_percentage} />
                    <dl className="host-hit-metrics">
                      {evidence.query_coverage_percentage != null && (
                        <div className="host-hit-coverage">
                          <dt>Query coverage</dt>
                          <dd>
                            <span className="num">
                              {formatPercent(evidence.query_coverage_percentage)}
                            </span>
                            <Meter value={evidence.query_coverage_percentage} />
                          </dd>
                        </div>
                      )}
                      {evidence.subject_coverage_percentage != null && (
                        <div className="host-hit-coverage">
                          <dt>Subject coverage</dt>
                          <dd>
                            <span className="num">
                              {formatPercent(evidence.subject_coverage_percentage)}
                            </span>
                            <Meter value={evidence.subject_coverage_percentage} />
                          </dd>
                        </div>
                      )}
                      <div>
                        <dt>Alignment length</dt>
                        <dd className="num">{evidence.alignment_length}</dd>
                      </div>
                      <div>
                        <dt>E-value</dt>
                        <dd className="num">{formatEvalue(evidence.e_value)}</dd>
                      </div>
                    </dl>
                    <p className="evidence-item-meta">
                      <span>Source: {evidence.source}</span>
                      <ConfidenceBadge confidence={evidence.confidence} />
                    </p>
                  </div>
                ))}
              </div>

              {hits.length > HOST_SIMILARITY_PAGE_SIZE && (
                <div className="evidence-controls host-similarity-controls">
                  <span className="evidence-count host-similarity-count">
                    Showing {shown} of {hits.length} matches
                  </span>

                  <div className="evidence-control-buttons">
                    {visibleHostCount < hits.length && (
                      <button
                        type="button"
                        className="load-more-button host-similarity-load-more"
                        onClick={() =>
                          setVisibleHostCount((current) =>
                            Math.min(
                              current + HOST_SIMILARITY_PAGE_SIZE,
                              hits.length,
                            ),
                          )
                        }
                      >
                        Load more
                      </button>
                    )}
                    {visibleHostCount > HOST_SIMILARITY_PAGE_SIZE && (
                      <button
                        type="button"
                        className="load-more-button load-more-secondary host-similarity-show-fewer"
                        onClick={() =>
                          setVisibleHostCount(HOST_SIMILARITY_PAGE_SIZE)
                        }
                      >
                        Show fewer
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })()}


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

        <p className="section-sub">What the measurements suggest, each with its category and confidence.</p>

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
                  <p className="interpretation-meta">
                    {interpretation.category && (
                      <span className="badge badge-neutral">
                        Category: {String(interpretation.category).replaceAll("_", " ")}
                      </span>
                    )}
                    <ConfidenceBadge confidence={interpretation.confidence} />
                  </p>
                </div>
              ),
            )}
          </div>
        )}
      </section>

      
      <section className="analysis-report-section">
        <h3>Candidate Assessment</h3>
        <p className="section-sub">A summary of the case for and against this protein as a target.</p>

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
        <p className="section-sub">What this report cannot tell you.</p>

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
        <p className="section-sub">Short stretches of the protein that may be worth testing.</p>
        {peptideCandidates.length === 0 ? (
          <p>No peptide candidates are available.</p>
        ) : (
          <>
            <p className="peptide-candidate-count">
              {peptideCandidates.length} peptide candidates
            </p>

            <div
              className="report-table-wrapper peptide-candidates-table-wrapper"
              data-testid="peptide-candidates-list"
              tabIndex={0}
              role="region"
              aria-label="Peptide candidates, scrollable"
            >
              <table className="report-table">
                <thead>
                  <tr>
                    <th>Start</th>
                    <th>End</th>
                    <th>Length</th>
                    <th>Sequence</th>
                    <th>GRAVY</th>
                    <th>Net charge</th>
                    <th>Transmembrane overlap</th>
                  </tr>
                </thead>

                <tbody>
                  {peptideCandidates
                    .slice(0, visiblePeptideCount)
                    .map((candidate, index) => (
                      <tr
                        key={`${candidate.start}-${candidate.end}-${index}`}
                      >
                        <td>{candidate.start}</td>
                        <td>{candidate.end}</td>
                        <td>{candidate.length}</td>
                        <td className="sequence-cell">
                          {candidate.sequence}
                        </td>
                        <td>{formatNumber(candidate.gravy, { fallback: "Not available" })}</td>
                        <td>{formatSigned(candidate.net_charge, { fallback: "Not available" })}</td>
                        <td>
                          {candidate.overlaps_transmembrane == null
                            ? "Not available"
                            : candidate.overlaps_transmembrane
                              ? "Yes"
                              : "No"}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>

            {peptideCandidates.length > 10 && (
              <div className="peptide-candidates-controls">
                <span className="peptide-candidates-visible-count">
                  Showing {Math.min(
                    visiblePeptideCount,
                    peptideCandidates.length
                  )} of {peptideCandidates.length} candidates
                </span>

                {visiblePeptideCount < peptideCandidates.length ? (
                  <button
                    type="button"
                    className="peptide-candidates-toggle"
                    onClick={() =>
                      setVisiblePeptideCount((current) =>
                        Math.min(
                          current + 10,
                          peptideCandidates.length
                        )
                      )
                    }
                  >
                    Show 10 more candidates
                  </button>
                ) : (
                  <button
                    type="button"
                    className="peptide-candidates-toggle"
                    onClick={() => setVisiblePeptideCount(10)}
                  >
                    Show fewer candidates
                  </button>
                )}
              </div>
            )}
          </>
        )}
      </section>
    </div>
  )
}

export default AnalysisReport