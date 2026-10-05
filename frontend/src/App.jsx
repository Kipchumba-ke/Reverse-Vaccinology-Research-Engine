import { useEffect ,useState } from "react"
import { submitAnalysis, getAnalysisStatus } from './services/analysisService'
import AnalysisReport from "./components/AnalysisReport"
import './App.css'


function App() {
  const [submitted, setSubmitted] = useState(false) 
  const [sequence, setSequence] = useState('')
  const [error, setError] = useState(null)
  const [analysisId, setAnalysisId] = useState('')
  const [status, setStatus] = useState('')
  const [report, setReport] = useState(null)

  useEffect(() => {
    if (!analysisId) return

    let cancelled = false
    let timeoutId


    async function pollAnalysisStatus() {
      const result = await getAnalysisStatus(analysisId)

      if (cancelled) return

      setStatus(result.status)
      setReport(result.report)
      
      if (result.status === 'pending' || result.status === 'running') {
        timeoutId = setTimeout(pollAnalysisStatus, 1000)
      }

    }

    pollAnalysisStatus()
    
    return () => {
      cancelled = true
      clearTimeout(timeoutId)
    }

  }, [analysisId])


  async function handleSubmit() {
    try {
      const result = await submitAnalysis(sequence)

      setAnalysisId(result.analysis_id)

      setSubmitted(true)

    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <main className="analysis-page">
      <h1>Reverse Vaccinology</h1>
      <div className="analysis-form">
        <label htmlFor="protein-sequence">
          Protein Sequence
        </label>

        <textarea 
          id="protein-sequence" 
          name="protein-sequence" 
          value={sequence}
          onChange={(e) => setSequence(e.target.value)}
        />

        <button type="button" className="analysis-submit" onClick={handleSubmit}>
          Analyze Protein
        </button>
      </div>

      {report && (
        <AnalysisReport report={report} />
      )}

      {status && (
        <p>
          Analysis Status: {status}
        </p>
      )}

      {status === 'failed' && (
        <p>
          Analysis failed. Please try again.
        </p>
      )}

      {analysisId && (
        <p>
          Analysis ID: {analysisId}
        </p>
      )}

      {submitted && (
        <p>
          Analysis submitted!
        </p>
      )}

      {error && (
        <p>
          {error}
        </p>
      )}
    </main>
  )
}

export default App
