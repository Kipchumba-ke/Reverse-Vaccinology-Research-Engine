import { useEffect ,useState } from "react"
import { submitAnalysis, submitFastaAnalysis ,getAnalysisStatus, downloadAnalysisReport } from './services/analysisService'
import AnalysisReport from "./components/AnalysisReport"
import Register from './components/Register'
import Login from "./components/Login"
import MultiSequenceReport from "./components/MultiSequenceReport"
import LandingPage from './components/LandingPage'
import './App.css'



function App() {
  const [authenticated, setAuthenticated] = useState(
    Boolean(localStorage.getItem('token')),
  )
  const [view, setView] = useState('landing')

  if (authenticated) {
    return <AnalysisApp />
  }

  if (view === 'register') {
    return (
      <Register
        onRegister={() => setView('login')}
        onLogin={() => setView('login')}
      />
    )
  }

  if (view === 'login') {
    return (
      <Login
        onLogin={() => setAuthenticated(true)}
        onRegister={() => setView('register')}
      />
    )
  }

  return (
    <LandingPage
      onLogin={() => setView('login')}
      onRegister={() => setView('register')}
    />
  )
}


function AnalysisApp() {
  const [submitted, setSubmitted] = useState(false) 
  const [sequence, setSequence] = useState('')
  const [error, setError] = useState(null)
  const [analysisId, setAnalysisId] = useState('')
  const [status, setStatus] = useState('')
  const [report, setReport] = useState(null)
  const [fastaFile, setFastaFile] = useState(null)

  useEffect(() => {
    if (!analysisId) return

    let cancelled = false
    let timeoutId


    async function pollAnalysisStatus() {
      const token = localStorage.getItem('token')
      const result = await getAnalysisStatus(analysisId, token)

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
  setError(null)

  try {
    const token = localStorage.getItem('token')
    let result

    if (fastaFile) {
      const allowedExtensions = /\.(fasta|fa|fna)$/i

      if (!allowedExtensions.test(fastaFile.name)) {
        setError('Please select a .fasta, .fa, or .fna file.')
        return
      }

      const fastaContent = await fastaFile.text()

      if (!fastaContent.trim()) {
        setError('The selected FASTA file is empty.')
        return
      }

      result = await submitFastaAnalysis(fastaContent, token)
    } else {
      if (!sequence.trim()) {
        setError('Enter a protein sequence or select a FASTA file.')
        return
      }

      result = await submitAnalysis(sequence, token)
    }

    if (!result.analysis_id) {
      throw new Error(result.error || 'Unable to submit the analysis.')
    }

    setAnalysisId(result.analysis_id)
    setSubmitted(true)
  } catch (err) {
    setError(err.message || 'Analysis submission failed.')
  }
}

async function handleDownloadReport() {
  setError(null)

  try {
    const token = localStorage.getItem('token')

    await downloadAnalysisReport(analysisId, token)
  } catch (downloadError) {
    setError(downloadError.message || 'Unable to download the report.')
  }
}

  return (
    <main className="analysis-page">
      <h1>Reverse Vaccinology</h1>
      <div className="analysis-form">
        <label htmlFor="protein-sequence">
          Protein Sequence
        </label>

        <p className="input-help" id="protein-sequence-help">
          Paste a single protein sequence using the standard one-letter amino acid codes.
        </p>

        <textarea 
          id="protein-sequence" 
          name="protein-sequence"
          aria-describedby="protein-sequence-help"
          value={sequence}
          onChange={(e) => setSequence(e.target.value)}
        />


        <label htmlFor="fasta-file">
          Upload FASTA File
        </label>
        <p className="input-help" id="fasta-file-help">
          Alternatively, upload a .fasta, .fa, or .fna file. Multiple FASTA records
          can be analyzed together.
        </p>

        <input
          id="fasta-file"
          name="fasta-file"
          type="file"
          accept=".fasta,.fa,.fna"
          onChange={(event) => {
            setFastaFile(event.target.files?.[0] ?? null)
          }}
        />

        {fastaFile && (
          <p>
            Selected file: {fastaFile.name}
          </p>
        )}


        <button type="button" className="analysis-submit" onClick={handleSubmit}>
          Analyze Protein
        </button>
      </div>

      {report && (
        <>
          {Array.isArray(report.alignment) && Array.isArray(report.records)
            ? <MultiSequenceReport report={report} />
            : <AnalysisReport report={report} />}

          {status === 'completed' && (
            <button
              type="button"
              className="analysis-submit"
              onClick={handleDownloadReport}
            >
              Download PDF Report
            </button>
          )}
        </>
      )}


      {(status || submitted || error) && (
        <section
          className={`analysis-status-panel ${
            error || status === 'failed'
              ? 'status-failed'
              : status === 'completed'
                ? 'status-completed'
                : 'status-in-progress'
          }`}
          aria-live="polite"
          aria-atomic="true"
        >
          <div className="status-heading">
            <span className="status-indicator" aria-hidden="true">
              {status === 'completed'
                ? '✓'
                : error || status === 'failed'
                  ? '!'
                  : ''}
            </span>

            <div className="status-copy">
              <h3>
                {error || status === 'failed'
                  ? 'Analysis failed'
                  : status === 'completed'
                    ? 'Analysis completed'
                    : status === 'running'
                      ? 'Analysis in progress'
                      : status === 'pending'
                        ? 'Analysis queued'
                        : 'Submitting analysis'}
              </h3>

              <p>
                {error
                  ? error
                  : status === 'failed'
                    ? 'The analysis could not be completed. Please try again.'
                    : status === 'completed'
                      ? 'Your results are ready to review.'
                      : status === 'running'
                        ? 'Your protein sequence is being analyzed. This may take a little while.'
                        : 'Your request has been received and is waiting to be processed.'}
              </p>
            </div>

            {(status === 'pending' || status === 'running' || (!status && submitted)) && (
              <span className="status-spinner" aria-hidden="true" />
            )}
          </div>

          {analysisId && (
            <div className="status-id">
              <span>Analysis ID</span>
              <code>{analysisId}</code>
              <button
                type="button"
                className="copy-analysis-id"
                onClick={() => {
                  if (navigator.clipboard?.writeText) {
                    navigator.clipboard.writeText(analysisId)
                  }
                }}
                aria-label="Copy analysis ID"
                title="Copy analysis ID"
              >
                Copy
              </button>
            </div>
          )}
        </section>
      )}
    </main>
  )
}

export default App
