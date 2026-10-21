
import { useEffect, useState } from 'react'
import {
  Link,
  Navigate,
  Route,
  Routes,
  useNavigate,
  useParams,
} from 'react-router-dom'

import {
  submitAnalysis,
  submitFastaAnalysis,
  getAnalysisStatus,
  downloadAnalysisReport,
} from './services/analysisService'

import AnalysisReport from './components/AnalysisReport'
import AnalysisHistory from './components/AnalysisHistory'
import Register from './components/Register'
import Login from './components/Login'
import MultiSequenceReport from './components/MultiSequenceReport'
import LandingPage from './components/LandingPage'
import './App.css'

const ACTIVE_ANALYSIS_KEY = 'activeAnalysisId'

function ProtectedRoute({ authenticated, children }) {
  return authenticated ? children : <Navigate to="/login" replace />
}

function App() {
  const navigate = useNavigate()
  const [authenticated, setAuthenticated] = useState(
    Boolean(localStorage.getItem('token')),
  )

  return (
    <Routes>
      <Route
        path="/"
        element={
          authenticated ? (
            <Navigate to="/analyses" replace />
          ) : (
            <LandingPage
              onLogin={() => navigate('/login')}
              onRegister={() => navigate('/register')}
            />
          )
        }
      />

      <Route
        path="/login"
        element={
          authenticated
            ? <Navigate to="/analyses" replace />
            : <Login onLogin={() => setAuthenticated(true)} />
        }
      />

      <Route
        path="/register"
        element={
          authenticated ? (
            <Navigate to="/analyses" replace />
          ) : (
            <Register
              onRegister={() => navigate('/login')}
              onLogin={() => navigate('/login')}
            />
          )
        }
      />

      <Route
        path="/analyses/:analysisId?"
        element={
          <ProtectedRoute authenticated={authenticated}>
            <AuthenticatedLayout onLogout={() => setAuthenticated(false)}>
              <AnalysisWorkspace />
            </AuthenticatedLayout>
          </ProtectedRoute>
        }
      />

      <Route
        path="/history"
        element={
          <ProtectedRoute authenticated={authenticated}>
            <AuthenticatedLayout onLogout={() => setAuthenticated(false)}>
              <AnalysisHistory />
            </AuthenticatedLayout>
          </ProtectedRoute>
        }
      />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function AuthenticatedLayout({ children, onLogout }) {
  const navigate = useNavigate()

  function handleLogout() {
    localStorage.removeItem('token')
    localStorage.removeItem(ACTIVE_ANALYSIS_KEY)
    onLogout()
    navigate('/login', { replace: true })
  }

  return (
    <>
      <nav className="app-navigation" aria-label="Main navigation">
        <Link to="/analyses">New analysis</Link>
        <Link to="/history">Analysis history</Link>
        <button type="button" onClick={handleLogout}>Log out</button>
      </nav>
      {children}
    </>
  )
}

function AnalysisWorkspace() {
  const { analysisId: routeAnalysisId } = useParams()
  const navigate = useNavigate()

  const [submitted, setSubmitted] = useState(false)
  const [sequence, setSequence] = useState('')
  const [error, setError] = useState(null)
  const [analysisId, setAnalysisId] = useState(routeAnalysisId || '')
  const [status, setStatus] = useState('')
  const [report, setReport] = useState(null)
  const [fastaFile, setFastaFile] = useState(null)

  useEffect(() => {
    if (routeAnalysisId) {
      setAnalysisId(routeAnalysisId)
    }
    setError(null)
  }, [routeAnalysisId])

  useEffect(() => {
    setAnalysisId(routeAnalysisId || '')
    setError(null)
  }, [routeAnalysisId])

  useEffect(() => {
    if (!analysisId) return undefined

    let cancelled = false
    let timeoutId

    async function pollAnalysisStatus() {
      try {
        const token = localStorage.getItem('token')

        if (!token) {
          throw new Error('Your session has ended. Please log in again.')
        }

        const result = await getAnalysisStatus(analysisId, token)

        if (cancelled) return

        setStatus(result.status)
        setReport(result.report || null)
        setError(null)

        if (result.status === 'pending' || result.status === 'running') {
          timeoutId = setTimeout(pollAnalysisStatus, 1000)
        }
      } catch (err) {
        if (cancelled) return
        setError(err.message || 'Unable to retrieve analysis status.')
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
    setReport(null)
    setStatus('')
    setSubmitted(false)

    try {
      const token = localStorage.getItem('token')
      if (!token) throw new Error('Please log in before submitting an analysis.')

      let result

      if (fastaFile) {
        if (!/\.(fasta|fa|fna)$/i.test(fastaFile.name)) {
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
      setStatus(result.status || 'pending')
      setReport(result.report || null)
      setSubmitted(true)
      navigate(`/analyses/${result.analysis_id}`)
    } catch (err) {
      setError(err.message || 'Analysis submission failed.')
    }
  }

  async function handleDownloadReport() {
    setError(null)

    try {
      const token = localStorage.getItem('token')
      await downloadAnalysisReport(analysisId, token)
    } catch (err) {
      setError(err.message || 'Unable to download the report.')
    }
  }
  return (
    <main className="analysis-page">
      <h1>Reverse Vaccinology</h1>

      <div className="analysis-form">
        <label htmlFor="protein-sequence">Protein Sequence</label>
        <p className="input-help" id="protein-sequence-help">
          Paste a single protein sequence using the standard one-letter amino acid codes.
        </p>

        <textarea
          id="protein-sequence"
          name="protein-sequence"
          aria-describedby="protein-sequence-help"
          value={sequence}
          onChange={(event) => setSequence(event.target.value)}
        />

        <label htmlFor="fasta-file">Upload FASTA File</label>
        <p className="input-help" id="fasta-file-help">
          Alternatively, upload a .fasta, .fa, or .fna file. Multiple FASTA records
          can be analyzed together.
        </p>

        <input
          id="fasta-file"
          name="fasta-file"
          type="file"
          accept=".fasta,.fa,.fna"
          onChange={(event) => setFastaFile(event.target.files?.[0] ?? null)}
        />

        {fastaFile && <p>Selected file: {fastaFile.name}</p>}

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
              {status === 'completed' ? '✓' : error || status === 'failed' ? '!' : ''}
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
                onClick={() => navigator.clipboard?.writeText(analysisId)}
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

