import { useState } from 'react'
import AnalysisReport from './AnalysisReport'


function MultiSequenceReport({ report }) {
  const records = report.records ?? []
  const alignment = report.alignment ?? []
  const conservation = report.conservation ?? {}
  const proteinAnalyses = report.protein_analyses ?? []

  const [selectedProteinIndex, setSelectedProteinIndex] = useState(0)

  const selectedProteinReport = proteinAnalyses[selectedProteinIndex]

  return (
    <div className="analysis-report multi-sequence-report">
      <h2>Multiple-Sequence Analysis Report</h2>

      <section className="analysis-report-section">
        <h3>Sequence Summary</h3>
        <p>Sequences analyzed: {conservation.sequence_count ?? records.length}</p>
        <p>Alignment length: {conservation.alignment_length ?? alignment[0]?.length ?? 0}</p>
      </section>

      <section className="analysis-report-section">
        <h3>Multiple-Sequence Alignment</h3>

        {alignment.length > 0 ? (
          <div className="alignment-table-container">
            <table aria-label="Multiple-sequence alignment" className="alignment-table">
              <thead>
                <tr>
                  <th scope="col">Protein</th>
                  <th scope="col">Aligned sequence</th>
                </tr>
              </thead>
              <tbody>
                {alignment.map((alignedSequence, index) => (
                  <tr key={`${records[index]?.id ?? 'protein'}-${index}`}>
                    <th scope="row">
                      {records[index]?.id ?? `Protein ${index + 1}`}
                    </th>
                    <td>
                      <code>{alignedSequence}</code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p>No alignment is available for this analysis.</p>
        )}
      </section>

      <section className="analysis-report-section">
        <h3>Conservation</h3>
        {conservation.sequence_count != null && (
          <p>Sequences analyzed: {conservation.sequence_count}</p>
        )}
        {conservation.alignment_length != null && (
          <p>Alignment length: {conservation.alignment_length}</p>
        )}
        {conservation.conservation_percentage != null && (
          <p>
            Conservation: {' '}
            {Number(conservation.conservation_percentage).toFixed(2)}%
          </p>
        )}
        {conservation.regions?.length > 0 && (
          <>
            <h4>Conserved Regions</h4>
            <ul>
              {conservation.regions.map((region, index) => (
                <li key={`${region.start}-${region.end}-${index}`}>
                  Positions {region.start}–{region.end}
                </li>
              ))}
            </ul>
          </>
        )}
      </section>

      {proteinAnalyses.length > 0 && (
        <section className="analysis-report-section">
          <h3>Individual Protein Analysis</h3>

          <div className='protein-report-selector'>
            <label htmlFor="protein-report-select">
              Select protein report
            </label>

            <select
              id="protein-report-select"
              value={selectedProteinIndex}
              onChange={(event) =>
                setSelectedProteinIndex(Number(event.target.value))
              }
            >
              {proteinAnalyses.map((proteinReport, index) => {
                const proteinId =
                  proteinReport.protein?.id ??
                  proteinReport.protein_id ??
                  records[index]?.id ??
                  `Protein ${index + 1}`

                return (
                  <option
                    key={`${proteinId}-${index}`}
                    value={index}
                  >
                    {proteinId}
                  </option>
                )
              })}
            </select>
          </div>

          {selectedProteinReport && (
            <div className='individual-protein-report'>
              <AnalysisReport
                report={selectedProteinReport}
                title={`Protein Report: ${
                  selectedProteinReport.protein?.id ??
                  selectedProteinReport.protein_id ??
                  records[selectedProteinIndex]?.id ??
                  `Protein ${selectedProteinIndex + 1}`
                }`}
              />
            </div>
          )}
        </section>
      )}
    </div>
  )
}

export default MultiSequenceReport
